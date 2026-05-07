"""
Application configuration using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="Dashboard Analytics API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/dashboard_api",
        alias="DATABASE_URL"
    )
    
    # Gateway
    gateway_url: str = Field(default="http://localhost:3000/api", alias="GATEWAY_URL")
    gateway_auth_email: str = Field(default="admin@efko.local", alias="GATEWAY_AUTH_EMAIL")
    gateway_auth_password: str = Field(default="Efko2024!", alias="GATEWAY_AUTH_PASSWORD")
    gateway_timeout_connect: float = Field(default=10.0, alias="GATEWAY_TIMEOUT_CONNECT")
    gateway_timeout_read: float = Field(default=30.0, alias="GATEWAY_TIMEOUT_READ")
    gateway_max_retries: int = Field(default=3, alias="GATEWAY_MAX_RETRIES")
    
    # Sync Configuration
    sync_interval_minutes: int = Field(default=60, alias="SYNC_INTERVAL_MINUTES")
    retention_days: int = Field(default=90, alias="RETENTION_DAYS")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="logs/dashboard_api.log", alias="LOG_FILE")

    # RabbitMQ
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost:5672/",
        alias="RABBITMQ_URL"
    )
    rabbitmq_exchange: str = Field(
        default="efko.production.events",
        alias="RABBITMQ_EXCHANGE"
    )
    rabbitmq_queue_prefix: str = Field(
        default="analytics",
        alias="RABBITMQ_QUEUE_PREFIX"
    )
    rabbitmq_prefetch_count: int = Field(
        default=10,
        alias="RABBITMQ_PREFETCH_COUNT"
    )
    rabbitmq_enabled: bool = Field(
        default=True,
        alias="RABBITMQ_ENABLED"
    )
    
    # API
    default_page_size: int = 100
    cors_origins: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


settings = Settings()
