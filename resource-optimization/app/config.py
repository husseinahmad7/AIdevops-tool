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
    influxdb_url: str = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
    infrastructure_monitor_url: str = os.getenv(
        "INFRASTRUCTURE_MONITOR_URL", "http://infrastructure-monitor:8082"
    )

    class Config:
        env_file = ".env"


settings = Settings()
