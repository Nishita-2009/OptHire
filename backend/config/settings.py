"""
OptHire Application Configuration and Settings.
Loads environment settings with secure defaults.
"""
import os
from typing import List
from utils.config import GOOGLE_API_KEY


class Settings:
    """Application settings with environment variable fallbacks."""

    APP_NAME: str = "OptHire API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1")

    # Security & CORS: Defaults allow common local dev ports, configurable via CORS_ORIGINS
    _cors_env: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173")
    CORS_ORIGINS: List[str] = [origin.strip() for origin in _cors_env.split(",") if origin.strip()]

    # Database configuration: defaults to local SQLite, easily switchable to PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./opthire.db")

    # File upload constraints
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))  # 10 MB
    ALLOWED_EXTENSIONS: set = {".pdf"}
    ALLOWED_CONTENT_TYPES: set = {"application/pdf", "application/x-pdf", "binary/octet-stream"}

    # Model defaults matching existing OptHire configuration
    GEMINI_MODEL: str = "gemini-2.5-flash"
    DEFAULT_TEMPERATURE: float = 0.0

    @property
    def google_api_key(self) -> str:
        return GOOGLE_API_KEY


settings = Settings()
