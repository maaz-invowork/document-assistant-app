from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str
    QDRANT_DB_PATH: str = "./data/qdrant_db"
    UPLOAD_DIR: str = "./data/uploads"
    COLLECTION_NAME: str = "pdf_documents"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()