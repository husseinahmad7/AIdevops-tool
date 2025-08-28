import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    auth_enabled: bool = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    user_management_url: str = os.getenv(
        "USER_MANAGEMENT_URL", "http://user-management:8081"
    )
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://aidevops:aidevops_password@postgres:5432/aidevops"
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # Report storage
    reports_storage_path: str = os.getenv("REPORTS_STORAGE_PATH", "/app/reports")

    # External service URLs
    infrastructure_monitor_url: str = os.getenv(
        "INFRASTRUCTURE_MONITOR_URL", "http://infrastructure-monitor:8082"
    )
    ai_prediction_url: str = os.getenv("AI_PREDICTION_URL", "http://ai-prediction:8083")
    log_analysis_url: str = os.getenv("LOG_ANALYSIS_URL", "http://log-analysis:8084")
    resource_optimization_url: str = os.getenv(
        "RESOURCE_OPTIMIZATION_URL", "http://resource-optimization:8086"
    )

    class Config:
        env_file = ".env"


settings = Settings()
