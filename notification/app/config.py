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
    rabbitmq_url: str = os.getenv(
        "RABBITMQ_URL", "amqp://aidevops:aidevops_password@rabbitmq:5672/"
    )

    # Email settings
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")

    # Slack settings
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    slack_bot_token: str = os.getenv("SLACK_BOT_TOKEN", "")

    class Config:
        env_file = ".env"


settings = Settings()
