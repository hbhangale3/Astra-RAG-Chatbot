from pathlib import Path
from fastapi import UploadFile, HTTPException
import chromadb

from src.rag_doc_ingestion.ingest_doc import build_vector_store_from_uploaded_documents


DEFAULT_USER_ID = "default_user"
BASE_DATA_DIR = Path("data/users")
COLLECTION_NAME = "document_collection"

# Total storage allowed per user for uploaded PDFs.
MAX_USER_STORAGE_MB = 100
MAX_USER_STORAGE_BYTES = MAX_USER_STORAGE_MB * 1024 * 1024


def get_user_upload_dir(user_id: str = DEFAULT_USER_ID) -> Path:
    """
    Returns the upload directory for a specific user.

    Creates the directory if it does not already exist.
    """
    upload_dir = BASE_DATA_DIR / user_id / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def get_user_chroma_dir(user_id: str = DEFAULT_USER_ID) -> Path:
    """
    Returns the ChromaDB directory for a specific user.

    Creates the directory if it does not already exist.
    """
    chroma_dir = BASE_DATA_DIR / user_id / "chroma"
    chroma_dir.mkdir(parents=True, exist_ok=True)
    return chroma_dir


def clean_filename(filename: str) -> str:
    """
    Sanitizes the uploaded filename.

    This prevents path traversal issues such as '../../file.pdf'.
    """
    return Path(filename).name.replace(" ", "_")


def get_current_storage_usage_bytes(user_id: str = DEFAULT_USER_ID) -> int:
    """
    Calculates total storage currently used by the user's uploaded PDFs.
    """
    upload_dir = get_user_upload_dir(user_id)
    return sum(file.stat().st_size for file in upload_dir.glob("*.pdf"))


def get_storage_summary(user_id: str = DEFAULT_USER_ID) -> dict:
    """
    Returns storage quota information for the user.
    """
    used_bytes = get_current_storage_usage_bytes(user_id)

    return {
        "user_id": user_id,
        "used_mb": round(used_bytes / (1024 * 1024), 2),
        "limit_mb": MAX_USER_STORAGE_MB,
        "remaining_mb": round((MAX_USER_STORAGE_BYTES - used_bytes) / (1024 * 1024), 2),
    }


def rebuild_user_chroma(user_id: str = DEFAULT_USER_ID) -> None:
    """
    Rebuilds the user's ChromaDB collection from all PDFs in the uploads folder.

    MVP behavior:
    - Delete old collection.
    - Rebuild collection from remaining uploaded PDFs.

    Future improvement:
    - Replace this with incremental ingestion.
    """
    upload_dir = get_user_upload_dir(user_id)
    chroma_dir = get_user_chroma_dir(user_id)

    pdf_files = list(upload_dir.glob("*.pdf"))

    # If no PDFs are left, clear the Chroma collection.
    if not pdf_files:
        db = chromadb.PersistentClient(path=str(chroma_dir.resolve()))
        try:
            db.delete_collection(name=COLLECTION_NAME)
        except Exception:
            pass
        return

    ingestion_status = build_vector_store_from_uploaded_documents(
        docs_dir_path=str(upload_dir.resolve()),
        vector_store_path=str(chroma_dir.resolve()),
        collection_name=COLLECTION_NAME,
    )

    if ingestion_status != 0:
        raise HTTPException(
            status_code=500,
            detail="Document operation completed, but ChromaDB rebuild failed.",
        )


async def save_and_ingest_document(file: UploadFile, user_id: str = DEFAULT_USER_ID) -> dict:
    """
    Saves one uploaded PDF and rebuilds the user's ChromaDB collection.

    Flow:
    1. Validate file.
    2. Check storage quota.
    3. Save PDF to user's upload directory.
    4. Rebuild ChromaDB from all uploaded PDFs.
    5. Return uploaded file metadata.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for now.")

    upload_dir = get_user_upload_dir(user_id)

    safe_filename = clean_filename(file.filename)
    file_path = upload_dir / safe_filename

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    current_usage = get_current_storage_usage_bytes(user_id)

    # If this filename already exists, subtract its old size because it will be overwritten.
    existing_file_size = file_path.stat().st_size if file_path.exists() else 0

    projected_usage = current_usage - existing_file_size + len(content)

    if projected_usage > MAX_USER_STORAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Storage quota exceeded. Limit is {MAX_USER_STORAGE_MB} MB. "
                f"Current usage is {round(current_usage / (1024 * 1024), 2)} MB."
            ),
        )

    # Save uploaded PDF to disk.
    with open(file_path, "wb") as f:
        f.write(content)

    # Rebuild vector store from all current uploaded PDFs.
    rebuild_user_chroma(user_id)

    return {
        "filename": safe_filename,
        "path": str(file_path),
        "size_mb": round(len(content) / (1024 * 1024), 2),
        "user_id": user_id,
        "ingestion_status": "success",
    }


def list_user_documents(user_id: str = DEFAULT_USER_ID) -> list[dict]:
    """
    Lists all PDF documents uploaded by the user.
    """
    upload_dir = get_user_upload_dir(user_id)

    documents = []

    for file in upload_dir.glob("*.pdf"):
        documents.append(
            {
                "filename": file.name,
                "path": str(file),
                "size_mb": round(file.stat().st_size / (1024 * 1024), 2),
                "user_id": user_id,
            }
        )

    return documents


def delete_user_document(filename: str, user_id: str = DEFAULT_USER_ID) -> dict:
    """
    Deletes a specific uploaded PDF and rebuilds ChromaDB.

    Flow:
    1. Sanitize filename.
    2. Delete file from uploads directory.
    3. Rebuild ChromaDB from remaining PDFs.
    4. Return updated document and storage information.
    """
    upload_dir = get_user_upload_dir(user_id)
    safe_filename = clean_filename(filename)
    file_path = upload_dir / safe_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found.")

    if file_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF deletion is supported.")

    file_path.unlink()

    # Rebuild ChromaDB so deleted document chunks are removed from retrieval.
    rebuild_user_chroma(user_id)

    return {
        "message": "Document deleted successfully.",
        "deleted_file": safe_filename,
        "documents": list_user_documents(user_id),
        "storage": get_storage_summary(user_id),
    }