from dotenv import load_dotenv
from pydantic_settings import BaseSettings

#load env variables from the env file

load_dotenv()


class DocIngestionSettings(BaseSettings):
    DOCUMENTS_DIR: str
    VECTOR_STORE_DIR : str
    COLLECTION_NAME: str

    class config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"