from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    AIMINO_API_PREFIX: str = "/api/v1"
    AIMINO_SERVER_PORT: int = 8000
    AIMINO_ALLOWED_ORIGINS: List[str] = ["*"]

    # Pydantic v2 config
    model_config = SettingsConfigDict(
        # Only load .env if it exists and is a regular file to avoid
        # blocking on special files or FIFOs that some systems expose.
        env_file=(".env" if Path(".env").is_file() else None),
        extra="ignore",  # ignore unrelated env vars like GOOGLE_API_KEY
    )


settings = Settings()
