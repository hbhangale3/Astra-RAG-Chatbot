import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    """
    Frontend settings for backend API endpoints.

    Local development:
        BACKEND_BASE_URL defaults to http://localhost:8000

    Docker Compose:
        BACKEND_BASE_URL should be http://backend:8000
    """

    BACKEND_BASE_URL: str = os.getenv(
        "BACKEND_BASE_URL",
        "http://localhost:8000",
    )

    @property
    def DOCUMENT_UPLOAD_URL(self) -> str:
        return f"{self.BACKEND_BASE_URL}/documents/upload"

    @property
    def DOCUMENT_LIST_URL(self) -> str:
        return f"{self.BACKEND_BASE_URL}/documents/list"

    @property
    def DOCUMENT_STORAGE_URL(self) -> str:
        return f"{self.BACKEND_BASE_URL}/documents/storage"

    @property
    def DOCUMENT_DELETE_BASE_URL(self) -> str:
        return f"{self.BACKEND_BASE_URL}/documents"

    @property
    def CHAT_ENDPOINT_URL(self) -> str:
        return f"{self.BACKEND_BASE_URL}/chat/answer"

    @property
    def QUIZ_GENERATE_URL(self) -> str:
        return f"{self.BACKEND_BASE_URL}/quiz/generate"

    @property
    def QUIZ_ATTEMPTS_URL(self) -> str:
        return f"{self.BACKEND_BASE_URL}/quiz/attempts"

    @property
    def QUIZ_SUMMARY_URL(self) -> str:
        return f"{self.BACKEND_BASE_URL}/quiz/summary"

    class Config:
        env_file = ".env"
        extra = "allow"