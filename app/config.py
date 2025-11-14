"""Application configuration"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    database_url: str = "postgresql://keepshot:keepshot@localhost:5432/keepshot"

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Monitoring
    default_check_interval: int = 60  # minutes
    max_concurrent_checks: int = 10

    # Storage
    storage_path: str = "/app/storage"
    max_file_size: int = 100  # MB

    # Optional: JWT (for reference implementation)
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 86400  # 24 hours

    # Optional: Webhook
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None

    # Optional: Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

# Ensure storage directory exists
os.makedirs(settings.storage_path, exist_ok=True)
os.makedirs(os.path.join(settings.storage_path, "images"), exist_ok=True)
os.makedirs(os.path.join(settings.storage_path, "videos"), exist_ok=True)
os.makedirs(os.path.join(settings.storage_path, "pdfs"), exist_ok=True)
os.makedirs(os.path.join(settings.storage_path, "files"), exist_ok=True)
