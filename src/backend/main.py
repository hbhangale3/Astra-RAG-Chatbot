import logging
from fastapi import FastAPI
from src.backend.api.chat import router as chat_router
from src.backend.api.document_router import router as document_router
from src.backend.config.backend_settings import BackendSettings
from src.backend.api.quiz_router import router as quiz_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI()
app.include_router(chat_router)
app.include_router(document_router)
app.include_router(quiz_router)

settings = BackendSettings()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
    )