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

    # --- Auth / JWT (Phase 2) ---
    # JWT_SECRET is a secret (>=256 bits). It is provided ONLY via env; the repo
    # ships a placeholder in .env.example and never a real value (Gate 8 FAIL-BLOCK).
    # The dev/test default below is NOT a real secret and must be overridden in
    # staging/production via the JWT_SECRET env var.
    jwt_secret: str = Field(default="dev-insecure-change-me-32bytes-minimum-0000")
    jwt_algorithm: Literal["HS256"] = Field(default="HS256")
    jwt_issuer: str = Field(default="jaxego")
    jwt_audience: str = Field(default="jaxego-api")
    access_token_minutes: int = Field(default=15)
    refresh_token_days: int = Field(default=30)

    # --- External integrations (Phase 4) — adapters; secrets only via env ---
    # In dev/test the factory returns Stub adapters (no network); these values are
    # only consulted by the real httpx adapters in staging/production.
    receita_base_url: str = Field(default="https://minhareceita.org")
    receita_brasilapi_url: str = Field(default="https://brasilapi.com.br/api/cnpj/v1")
    # Comma-separated host allowlist for the SSRF guard (TH-02/TH-03).
    receita_allowlist_hosts: str = Field(default="minhareceita.org,brasilapi.com.br")

    sms_zenvia_url: str = Field(default="https://api.zenvia.com/v2/channels/sms/messages")
    sms_zenvia_token: str | None = Field(default=None)
    sms_twilio_url: str | None = Field(default=None)
    sms_twilio_token: str | None = Field(default=None)
    sms_allowlist_hosts: str = Field(default="api.zenvia.com")

    ses_send_url: str = Field(default="https://email.sa-east-1.amazonaws.com/send")
    ses_api_token: str | None = Field(default=None)
    ses_allowlist_hosts: str = Field(default="email.sa-east-1.amazonaws.com")

    geocoding_base_url: str = Field(default="https://nominatim.openstreetmap.org")
    geocoding_allowlist_hosts: str = Field(default="nominatim.openstreetmap.org")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
