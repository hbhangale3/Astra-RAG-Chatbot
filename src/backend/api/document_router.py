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
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads one PDF document and ingests it into the user's ChromaDB store.
    """
    document = await save_and_ingest_document(file)

    return {
        "message": "Document uploaded and ingested successfully.",
        "document": document,
        "storage": get_storage_summary(),
    }


@router.get("/list")
def list_documents():
    """
    Returns all uploaded PDF documents for the default user.
    """
    return {
        "documents": list_user_documents(),
        "storage": get_storage_summary(),
    }


@router.get("/storage")
def get_storage():
    """
    Returns current storage usage and quota information.
    """
    return {
        "storage": get_storage_summary(),
    }


@router.delete("/{filename}")
def delete_document(filename: str):
    """
    Deletes one uploaded PDF and removes its vectors by rebuilding ChromaDB.
    """
    return delete_user_document(filename)