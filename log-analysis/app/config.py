import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Log Analysis Service"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Authentication settings
    AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "True").lower() == "true"
    USER_MANAGEMENT_URL: str = os.getenv(
        "USER_MANAGEMENT_URL", "http://user-management:8081"
    )

    # Elasticsearch settings
    ELASTICSEARCH_URL: str = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
    ELASTICSEARCH_USERNAME: str = os.getenv("ELASTICSEARCH_USERNAME", "")
    ELASTICSEARCH_PASSWORD: str = os.getenv("ELASTICSEARCH_PASSWORD", "")
    LOG_INDEX_PREFIX: str = os.getenv("LOG_INDEX_PREFIX", "aidevops-logs-")

    # Log ingestion settings
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", "1000"))
    LOG_RETENTION_DAYS: int = int(os.getenv("LOG_RETENTION_DAYS", "30"))

    # Redis settings for caching
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # seconds

    # RabbitMQ settings for alerts
    RABBITMQ_URL: str = os.getenv(
        "RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F"
    )
    ALERT_EXCHANGE: str = os.getenv("ALERT_EXCHANGE", "aidevops.alerts")

    # Kafka settings (optional)
    KAFKA_BROKER_URL: str = os.getenv("KAFKA_BROKER_URL", "kafka:9092")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "aidevops.log_anomalies")

    class Config:
        env_file = ".env"


settings = Settings()
