import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "AI Prediction Service"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Authentication settings
    AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "True").lower() == "true"
    USER_MANAGEMENT_URL: str = os.getenv("USER_MANAGEMENT_URL", "http://user-management:8081")
    
    # Model settings
    MODEL_DIR: str = os.getenv("MODEL_DIR", "./models")
    DEFAULT_FORECAST_DAYS: int = int(os.getenv("DEFAULT_FORECAST_DAYS", "7"))
    MAX_FORECAST_DAYS: int = int(os.getenv("MAX_FORECAST_DAYS", "30"))
    ANOMALY_DETECTION_THRESHOLD: float = float(os.getenv("ANOMALY_DETECTION_THRESHOLD", "0.95"))

    # MongoDB for model metadata
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "aidevops")

    # MLflow tracking
    MLFLOW_TRACKING_URI: str = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    MLFLOW_S3_ENDPOINT_URL: str = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://minio:9000")

    # S3/MinIO credentials
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "aidevops")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "aidevops_secret")

    # Redis settings for caching
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # seconds
    
    class Config:
        env_file = ".env"

settings = Settings()