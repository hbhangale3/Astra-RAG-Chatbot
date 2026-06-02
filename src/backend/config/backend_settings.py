from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class BackendSettings(BaseSettings):
    API_HOST : str = "localhost"
    API_PORT : int = 8000

    class config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"