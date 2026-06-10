"""Application settings — single source of environment configuration.

Reads from environment / `.env`. Secrets (SENTRY_DSN, DATABASE_URL credentials)
are provided only via env, never committed to the repo.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Environment / release metadata
    environment: Literal["dev", "staging", "production", "test"] = Field(default="dev")
    app_version: str = Field(default="0.1.0")

    # Datastores
    database_url: str = Field(
        default="mysql+aiomysql://jaxego:jaxego@localhost:3306/jaxego?charset=utf8mb4",
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Observability (optional — no-op when absent)
    sentry_dsn: str | None = Field(default=None)

    # Logging
    log_level: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
