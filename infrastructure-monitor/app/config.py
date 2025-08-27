import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Infrastructure Monitoring Service"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Authentication settings
    AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "True").lower() == "true"
    USER_MANAGEMENT_URL: str = os.getenv("USER_MANAGEMENT_URL", "http://user-management:8081")
    
    # Monitoring settings
    MONITORING_INTERVAL: int = int(os.getenv("MONITORING_INTERVAL", "60"))  # seconds
    METRICS_RETENTION_DAYS: int = int(os.getenv("METRICS_RETENTION_DAYS", "30"))
    
    # Redis settings for caching
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # seconds
    
    # RabbitMQ settings for alerts
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")
    ALERT_EXCHANGE: str = os.getenv("ALERT_EXCHANGE", "aidevops.alerts")
    
    # Docker monitoring
    DOCKER_ENABLED: bool = os.getenv("DOCKER_ENABLED", "True").lower() == "true"
    DOCKER_HOST: str = os.getenv("DOCKER_HOST", "unix://var/run/docker.sock")
    
    # Kubernetes monitoring
    K8S_ENABLED: bool = os.getenv("K8S_ENABLED", "False").lower() == "true"
    K8S_CONFIG_PATH: str = os.getenv("K8S_CONFIG_PATH", "")
    K8S_CONTEXT: str = os.getenv("K8S_CONTEXT", "")
    
    # Alert thresholds
    CPU_THRESHOLD: float = float(os.getenv("CPU_THRESHOLD", "80.0"))  # percentage
    MEMORY_THRESHOLD: float = float(os.getenv("MEMORY_THRESHOLD", "80.0"))  # percentage
    DISK_THRESHOLD: float = float(os.getenv("DISK_THRESHOLD", "85.0"))  # percentage
    
    class Config:
        env_file = ".env"

settings = Settings()