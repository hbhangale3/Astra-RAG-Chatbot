from fastapi import APIRouter, UploadFile, File

from src.backend.services.document_service import (
    save_and_ingest_document,
    list_user_documents,
    delete_user_document,
    get_storage_summary,
)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), user_id: str = "default_user"):
    """
    Uploads one PDF document and ingests it into the user's ChromaDB store.
    """
    document = await save_and_ingest_document(file,user_id=user_id)

    return {
        "message": "Document uploaded and ingested successfully.",
        "document": document,
        "storage": get_storage_summary(),
    }


@router.get("/list")
def list_documents(user_id: str = "default_user"):
    """
    Returns all uploaded PDF documents for the default user.
    """
    return {
        "documents": list_user_documents(user_id=user_id),
        "storage": get_storage_summary(user_id=user_id),
    }


@router.get("/storage")
def get_storage(user_id: str = "default_user"):
    """
    Returns current storage usage and quota information.
    """
    return {
        "storage": get_storage_summary(user_id=user_id),
    }


@router.delete("/{filename}")
def delete_document(filename: str, user_id: str = "default_user"):
    """
    Deletes one uploaded PDF and removes its vectors by rebuilding ChromaDB.
    """
    return delete_user_document(filename)