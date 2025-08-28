import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "AI DevOps Assistant Natural Language Interface"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # API Keys
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    # Vector DB settings
    VECTOR_DB_TYPE: str = os.getenv(
        "VECTOR_DB_TYPE", "chroma"
    )  # chroma, pinecone, etc.
    VECTOR_DB_URL: str = os.getenv("VECTOR_DB_URL", "")
    VECTOR_DB_API_KEY: str = os.getenv("VECTOR_DB_API_KEY", "")
    VECTOR_DB_ENVIRONMENT: str = os.getenv("VECTOR_DB_ENVIRONMENT", "")
    VECTOR_DB_INDEX_NAME: str = os.getenv("VECTOR_DB_INDEX_NAME", "aidevops-docs")

    # LLM settings
    LLM_PROVIDER: str = os.getenv(
        "LLM_PROVIDER", "openrouter"
    )  # openrouter, huggingface, ollama
    LLM_MODEL: str = os.getenv("LLM_MODEL", "mistralai/mistral-7b-instruct")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Embedding settings
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2"
    )

    # Document storage
    DOCUMENT_STORE_PATH: str = os.getenv("DOCUMENT_STORE_PATH", "./data/documents")

    # Authentication
    AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "True").lower() == "true"
    USER_MANAGEMENT_URL: str = os.getenv(
        "USER_MANAGEMENT_URL", "http://user-management:8081"
    )

    class Config:
        env_file = ".env"


settings = Settings()
