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

    # --- Backblaze B2 storage (Phase 5) — KYC documents, PRIVATE bucket ---
    # B2 is S3-compatible; we drive it with boto3 (S3v4). The KEY/APP_KEY are
    # SECRETS provided ONLY via env (Field default None — Gate 8 FAIL-BLOCK if a
    # real value lands in the repo). In dev/test the factory returns the Stub
    # adapter (filesystem temp, no network), so these are unused there.
    # If a secret is ever committed: ROTATE it in the B2 console immediately.
    b2_key_id: str | None = Field(default=None)
    b2_app_key: str | None = Field(default=None)
    b2_endpoint_url: str = Field(default="https://s3.us-west-004.backblazeb2.com")
    b2_region: str = Field(default="us-west-004")
    b2_kyc_bucket: str = Field(default="jaxego-kyc-prod")
    # Comma-separated host allowlist for the SSRF guard on the internal download
    # of the just-uploaded object (TH-04). Only the B2 S3 endpoint host.
    b2_allowlist_hosts: str = Field(default="s3.us-west-004.backblazeb2.com")

    # --- OSRM routing (Phase 8) — ETA/distance for the dispatch ranking ---
    # In dev/test the factory returns the haversine Stub (no network). The real
    # httpx adapter is wired in staging/production; it degrades to haversine ×1.4
    # (eta_degraded) on any error — it NEVER blocks the cascade (TH-8). The host
    # allowlist closes SSRF (TH-9 / A10) the same way as the other adapters.
    osrm_base_url: str = Field(default="https://router.project-osrm.org")
    osrm_profile: str = Field(default="driving")
    osrm_allowlist_hosts: str = Field(default="router.project-osrm.org")

    # --- Web Push VAPID (Phase 8) — offer/accept notifications ---
    # The VAPID PRIVATE key is a SECRET provided ONLY via env (Field default None —
    # Gate 8 FAIL-BLOCK if a real value lands in the repo; if committed, ROTATE).
    # In dev/test the factory returns the Push Stub (no network), so these are
    # unused there. The public key + claim subject are not secret.
    vapid_private_key: str | None = Field(default=None)
    vapid_public_key: str | None = Field(default=None)
    vapid_claim_sub: str = Field(default="mailto:ops@jaxego.com.br")

    # --- Safe2Pay payment core (Phase 10) — SECRETS only via env (Gate 8) ---
    # In dev/test the factory returns the PaymentStubAdapter (no network, no sandbox);
    # these are consulted only by the real httpx adapter in staging/production. Every
    # one of the secrets below is `Field(default=None)` — a real value committed to the
    # repo is a Gate 8 FAIL-BLOCK and MUST be ROTATED, not just removed from history.
    safe2pay_api_key: str | None = Field(default=None)
    safe2pay_sandbox: bool = Field(default=True)
    # 64 hex chars (32 bytes) for AES-256-GCM of the card token at rest (TH-B).
    safe2pay_token_encrypt_key: str | None = Field(default=None)
    # HMAC secret for the webhook signature ([ASSUMIDO A4] — confirm at T-13).
    safe2pay_webhook_secret: str | None = Field(default=None)
    # RSA-2048 keypair: private decrypts the card blob (backend only); public is served
    # to the client via GET /v1/payments/chave-publica. PEM or base64(PEM).
    rsa_private_key: str | None = Field(default=None)
    rsa_public_key: str | None = Field(default=None)
    # The 3 Safe2Pay subdomains (payment creates / api administers / services queries).
    # Separate base URLs — never concatenate a subdomain (skill A1). Each host is in the
    # SSRF allowlist (TH-L).
    safe2pay_payment_url: str = Field(default="https://payment.safe2pay.com.br")
    safe2pay_api_url: str = Field(default="https://api.safe2pay.com.br")
    safe2pay_services_url: str = Field(default="https://services.safe2pay.com.br")
    safe2pay_allowlist_hosts: str = Field(
        default="payment.safe2pay.com.br,api.safe2pay.com.br,services.safe2pay.com.br"
    )
    # The Jaxegô recipient id (the platform's own Safe2Pay subaccount for the fee).
    safe2pay_jaxego_recipient: str | None = Field(default=None)
    # Revenue share default (OQ-1 / A7) — parametrised, never hardcoded in code.
    revenue_share_default_pct: int = Field(default=20)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
