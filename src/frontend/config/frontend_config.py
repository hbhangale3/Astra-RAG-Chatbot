from pydantic_settings import BaseSettings
from dotenv import load_dotenv


load_dotenv()

class Settings(BaseSettings):
    CHAT_ENDPOINT_URL: str = "http://localhost:8000/chat/answer"
    DOCUMENT_UPLOAD_URL: str = "http://localhost:8000/documents/upload"
    DOCUMENT_LIST_URL: str = "http://localhost:8000/documents/list"
    DOCUMENT_STORAGE_URL: str = "http://localhost:8000/documents/storage"
    DOCUMENT_DELETE_BASE_URL: str = "http://localhost:8000/documents"

    class Config:
        env_file = ".env"
        extra="allow"