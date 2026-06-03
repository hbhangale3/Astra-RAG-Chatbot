from pathlib import Path
from fastapi import UploadFile, HTTPException

from src.rag_doc_ingestion.ingest_doc import build_vector_store_from_uploaded_documents


DEFAULT_USER_ID = "default_user"
BASE_DATA_DIR = Path("data/users")


def get_user_upload_dir(user_id: str = DEFAULT_USER_ID) -> Path:
    upload_dir = BASE_DATA_DIR / user_id / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def get_user_chroma_dir(user_id: str = DEFAULT_USER_ID) -> Path:
    chroma_dir = BASE_DATA_DIR / user_id / "chroma"
    chroma_dir.mkdir(parents=True, exist_ok=True)
    return chroma_dir


def clean_filename(filename: str) -> str:
    return Path(filename).name.replace(" ", "_")


async def save_and_ingest_document(file: UploadFile, user_id: str = DEFAULT_USER_ID) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for now.")

    upload_dir = get_user_upload_dir(user_id)
    chroma_dir = get_user_chroma_dir(user_id)

    safe_filename = clean_filename(file.filename)
    file_path = upload_dir / safe_filename

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    with open(file_path, "wb") as f:
        f.write(content)

    ingestion_status = build_vector_store_from_uploaded_documents(
        docs_dir_path=str(upload_dir.resolve()),
        vector_store_path=str(chroma_dir.resolve()),
        collection_name="document_collection",
    )

    if ingestion_status != 0:
        raise HTTPException(
            status_code=500,
            detail="File uploaded, but ingestion failed."
        )

    return {
        "filename": safe_filename,
        "path": str(file_path),
        "size_mb": round(len(content) / (1024 * 1024), 2),
        "user_id": user_id,
        "ingestion_status": "success",
    }


def list_user_documents(user_id: str = DEFAULT_USER_ID) -> list[dict]:
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