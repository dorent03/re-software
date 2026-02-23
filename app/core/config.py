"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings:
    """Central configuration sourced from environment variables."""

    APP_TITLE: str = "RE-Software Invoice Management API"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "Production-ready invoice management backend with e-invoicing"

    # MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "re_software")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-to-a-random-secret-key-at-least-32-chars")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # File storage
    UPLOAD_DIR: Path = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
    PDF_DIR: Path = BASE_DIR / os.getenv("PDF_DIR", "pdfs")

    # VAT rates (Germany)
    VAT_RATE_STANDARD: float = 0.19
    VAT_RATE_REDUCED: float = 0.07
    VAT_RATE_ZERO: float = 0.0

    ALLOWED_VAT_RATES: list = [0.19, 0.07, 0.0]

    # Default VAT rate
    DEFAULT_VAT_RATE: float = 0.19

    # Payment methods
    PAYMENT_METHODS: list = ["BANK", "CASH", "PAYPAL"]

    # Reminder settings
    MAX_REMINDER_LEVEL: int = 3


settings = Settings()

# Ensure storage directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.PDF_DIR.mkdir(parents=True, exist_ok=True)
