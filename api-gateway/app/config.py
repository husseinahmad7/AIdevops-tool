import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # API Gateway settings
    APP_NAME: str = "AI DevOps Assistant API Gateway"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://aidevops:aidevops_password@postgres:5432/aidevops")
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # RabbitMQ settings
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://aidevops:aidevops_password@rabbitmq:5672/")
    
    # JWT settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "supersecretkey")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Service URLs
    USER_MANAGEMENT_URL: str = os.getenv("USER_MANAGEMENT_URL", "http://user-management:8081")
    INFRASTRUCTURE_MONITOR_URL: str = os.getenv("INFRASTRUCTURE_MONITOR_URL", "http://infrastructure-monitor:8082")
    AI_PREDICTION_URL: str = os.getenv("AI_PREDICTION_URL", "http://ai-prediction:8083")
    LOG_ANALYSIS_URL: str = os.getenv("LOG_ANALYSIS_URL", "http://log-analysis:8084")
    CICD_OPTIMIZATION_URL: str = os.getenv("CICD_OPTIMIZATION_URL", "http://cicd-optimization:8085")
    RESOURCE_OPTIMIZATION_URL: str = os.getenv("RESOURCE_OPTIMIZATION_URL", "http://resource-optimization:8086")
    NATURAL_LANGUAGE_URL: str = os.getenv("NATURAL_LANGUAGE_URL", "http://natural-language:8088")
    NOTIFICATION_URL: str = os.getenv("NOTIFICATION_URL", "http://notification:8087")
    REPORTING_URL: str = os.getenv("REPORTING_URL", "http://reporting:8089")
    
    # API Keys
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    class Config:
        env_file = ".env"

settings = Settings()