"""Server configuration (stub) using pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    server_port: int = 8000
    server_host: str = "0.0.0.0"
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    allowed_origins: str = "*"

    class Config:
        env_prefix = "AIMINO_"


settings = Settings()  # loaded from env

__all__ = ["settings", "Settings"]

