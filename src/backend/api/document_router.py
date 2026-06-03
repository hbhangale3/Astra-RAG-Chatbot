from fastapi import APIRouter, UploadFile, File

from src.backend.services.document_service import (
    save_and_ingest_document,
    list_user_documents,
)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    document = await save_and_ingest_document(file)

    return {
        "message": "Document uploaded and ingested successfully.",
        "document": document,
    }


@router.get("/list")
def list_documents():
    return {
        "documents": list_user_documents()
    }