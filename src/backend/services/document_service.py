from pathlib import Path

import chromadb
from fastapi import HTTPException, UploadFile

from src.rag_doc_ingestion.ingest_doc import build_vector_store_from_uploaded_documents
from src.backend.services.metrics_service import (
    documents_uploaded_total,
    storage_used_bytes,
    ingestion_success_total,
    ingestion_failure_total,
)


DEFAULT_USER_ID = "default_user"
BASE_DATA_DIR = Path("data/users")
COLLECTION_NAME = "document_collection"

SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md"}

# Total storage allowed per user for uploaded documents.
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


def is_supported_document(filename: str) -> bool:
    """
    Checks whether the uploaded file extension is supported.

    Parameters:
        filename (str): Uploaded filename.

    Returns:
        bool: True if the extension is supported, otherwise False.
    """
    return Path(filename).suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS


def get_uploaded_document_paths(user_id: str = DEFAULT_USER_ID) -> list[Path]:
    """
    Returns all supported uploaded document paths for a user.

    Parameters:
        user_id (str): Authenticated user identifier.

    Returns:
        list[Path]: Uploaded document paths matching supported extensions.
    """
    upload_dir = get_user_upload_dir(user_id)

    return [
        file
        for file in upload_dir.iterdir()
        if file.is_file() and file.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS
    ]


def get_current_storage_usage_bytes(user_id: str = DEFAULT_USER_ID) -> int:
    """
    Calculates total storage currently used by the user's uploaded documents.
    """
    return sum(file.stat().st_size for file in get_uploaded_document_paths(user_id))


def update_storage_used_metric(user_id: str = DEFAULT_USER_ID) -> int:
    """
    Updates the Prometheus storage gauge for a user.

    Parameters:
        user_id (str): Authenticated user identifier.

    Returns:
        int: Current storage usage in bytes.
    """
    used_bytes = get_current_storage_usage_bytes(user_id)

    storage_used_bytes.labels(
        user_id=user_id,
    ).set(used_bytes)

    return used_bytes


def get_storage_summary(user_id: str = DEFAULT_USER_ID) -> dict:
    """
    Returns storage quota information for the user.
    """
    used_bytes = get_current_storage_usage_bytes(user_id)

    return {
        "user_id": user_id,
        "used_bytes": used_bytes,
        "used_mb": round(used_bytes / (1024 * 1024), 2),
        "limit_mb": MAX_USER_STORAGE_MB,
        "remaining_mb": round((MAX_USER_STORAGE_BYTES - used_bytes) / (1024 * 1024), 2),
    }


def rebuild_user_chroma(user_id: str = DEFAULT_USER_ID) -> None:
    """
    Rebuilds the user's ChromaDB collection from all supported uploaded documents.

    MVP behavior:
    - Delete old collection.
    - Rebuild collection from remaining uploaded documents.

    Future improvement:
    - Replace this with incremental ingestion.
    """
    upload_dir = get_user_upload_dir(user_id)
    chroma_dir = get_user_chroma_dir(user_id)

    uploaded_documents = get_uploaded_document_paths(user_id)

    # If no supported documents are left, clear the Chroma collection.
    if not uploaded_documents:
        db = chromadb.PersistentClient(path=str(chroma_dir.resolve()))

        try:
            db.delete_collection(name=COLLECTION_NAME)
        except Exception:
            pass

        # Empty document set is a successful Chroma cleanup operation.
        ingestion_success_total.labels(user_id=user_id).inc()
        return

    ingestion_status = build_vector_store_from_uploaded_documents(
        docs_dir_path=str(upload_dir.resolve()),
        vector_store_path=str(chroma_dir.resolve()),
        collection_name=COLLECTION_NAME,
    )

    if ingestion_status != 0:
        ingestion_failure_total.labels(user_id=user_id).inc()

        raise HTTPException(
            status_code=500,
            detail="Document operation completed, but ChromaDB rebuild failed.",
        )

    ingestion_success_total.labels(user_id=user_id).inc()


async def save_and_ingest_document(
    file: UploadFile,
    user_id: str = DEFAULT_USER_ID,
) -> dict:
    """
    Saves one uploaded document and rebuilds the user's ChromaDB collection.

    Flow:
    1. Validate file.
    2. Check storage quota.
    3. Save document to user's upload directory.
    4. Rebuild ChromaDB from all uploaded documents.
    5. Update Prometheus document/storage/ingestion metrics.
    6. Return uploaded file metadata.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing.")

    if not is_supported_document(file.filename):
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. Supported formats are: "
                "PDF, DOCX, PPTX, TXT, and MD."
            ),
        )

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

    # Save uploaded document to disk.
    with open(file_path, "wb") as f:
        f.write(content)

    # Rebuild vector store from all current uploaded documents.
    rebuild_user_chroma(user_id)

    # Count only successful upload + ingestion as uploaded.
    documents_uploaded_total.labels(user_id=user_id).inc()

    # Update current storage gauge after successful upload.
    used_bytes = update_storage_used_metric(user_id)

    return {
        "filename": safe_filename,
        "extension": file_path.suffix.lower(),
        "path": str(file_path),
        "size_mb": round(len(content) / (1024 * 1024), 2),
        "user_id": user_id,
        "used_bytes": used_bytes,
        "ingestion_status": "success",
    }


def list_user_documents(user_id: str = DEFAULT_USER_ID) -> list[dict]:
    """
    Lists all supported documents uploaded by the user.
    """
    documents = []

    for file in get_uploaded_document_paths(user_id):
        documents.append(
            {
                "filename": file.name,
                "extension": file.suffix.lower(),
                "path": str(file),
                "size_mb": round(file.stat().st_size / (1024 * 1024), 2),
                "user_id": user_id,
            }
        )

    # Keep storage gauge fresh when the frontend lists documents.
    update_storage_used_metric(user_id)

    return documents


def delete_user_document(filename: str, user_id: str = DEFAULT_USER_ID) -> dict:
    """
    Deletes a specific uploaded document and rebuilds ChromaDB.

    Flow:
    1. Sanitize filename.
    2. Delete file from uploads directory.
    3. Rebuild ChromaDB from remaining documents.
    4. Update Prometheus storage/ingestion metrics.
    5. Return updated document and storage information.
    """
    upload_dir = get_user_upload_dir(user_id)
    safe_filename = clean_filename(filename)
    file_path = upload_dir / safe_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found.")

    if not is_supported_document(file_path.name):
        raise HTTPException(
            status_code=400,
            detail="Only supported document deletion is allowed.",
        )

    file_path.unlink()

    # Rebuild ChromaDB so deleted document chunks are removed from retrieval.
    rebuild_user_chroma(user_id)

    # Update current storage gauge after successful deletion.
    update_storage_used_metric(user_id)

    return {
        "message": "Document deleted successfully.",
        "deleted_file": safe_filename,
        "documents": list_user_documents(user_id),
        "storage": get_storage_summary(user_id),
    }