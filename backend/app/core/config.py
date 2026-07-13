"""
Application configuration — loaded from environment variables.
"""

import os
from pathlib import Path

env_file = Path(__file__).resolve().parents[3] / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())


class Settings:
    APP_NAME: str = "Workforce Compliance AI"
    VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://workforce:workforce@localhost:5432/workforce_compliance"
    )

    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE-ME-IN-PRODUCTION-use-secrets-manager")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "480"))
    JWT_REFRESH_EXPIRATION_DAYS: int = 7

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8501").split(",")

    MAX_EMPLOYEES_PER_TENANT: int = 10000
    MAX_UPLOAD_SIZE_MB: int = 10


settings = Settings()
