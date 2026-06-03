from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path

#load env variables from the env file

load_dotenv()


class DocIngestionSettings(BaseSettings):
    DOCUMENTS_DIR: str
    VECTOR_STORE_DIR : str
    COLLECTION_NAME: str
    """This means locally:

        VECTOR_STORE_DIR=./vectorDB

        becomes something like:

        /Users/yourname/.../Astra-RAG-Chatbot/vectorDB

        And in Docker:

        VECTOR_STORE_DIR=/app/vectorDB

        stays:

        /app/vectorDB

        This removes ambiguity."""
    @field_validator("DOCUMENTS_DIR", "VECTOR_STORE_DIR")
    @classmethod
    def normalize_path(cls, value: str) -> str:
        cleaned = str(value).strip().strip('"').strip("'")
        return str(Path(cleaned).resolve())
    
    class config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"