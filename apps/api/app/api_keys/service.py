"""API key lifecycle (RN-020 / D-01) — generate, list, revoke.

The secret is generated with `secrets.token_urlsafe` and stored ONLY as its
argon2id hash (`app.core.security.hash_password`, the same argon2id used for auth
— ADR-005). The full token `jxg_<key_id>_<secret>` is returned ONCE at creation
and never reconstructable from the DB (TH-01 / TH-09). Revoke is a soft-revoke
(`revoked_at`) that invalidates the auth cache so propagation is < 1min (D-09).
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_keys import repo
from app.api_keys.dependencies import invalidate_api_key_cache
from app.api_keys.models import ApiKey
from app.api_keys.schemas import ALLOWED_SCOPES
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.security import hash_password

logger = structlog.get_logger("api_keys.service")

# `key_id` is the public lookup handle (16 url-safe chars ≈ 96 bits — non-secret).
_KEY_ID_BYTES = 12
# The secret is 256 bits (32 bytes url-safe) — the only credential, hashed at rest.
_SECRET_BYTES = 32


def _new_key_id() -> str:
    """A public, indexed lookup handle (non-secret)."""
    return secrets.token_urlsafe(_KEY_ID_BYTES).replace("-", "").replace("_", "")[:16]


def _new_secret() -> str:
    """A 256-bit secret (the only credential — stored as argon2id hash)."""
    return secrets.token_urlsafe(_SECRET_BYTES)


def compose_token(key_id: str, secret: str) -> str:
    """The full token the integrator stores: `jxg_<key_id>_<secret>`."""
    return f"jxg_{key_id}_{secret}"


def _validate_scopes(scopes: list[str]) -> str:
    """Validate + normalise the requested scopes to a stored space-separated string."""
    cleaned = sorted({s.strip() for s in scopes if s.strip()})
    if not cleaned:
        cleaned = ["deliveries:write"]
    for scope in cleaned:
        if scope not in ALLOWED_SCOPES:
            raise ValidationAppError(f"Escopo inválido: {scope}")
    return " ".join(cleaned)


async def create_api_key(
    session: AsyncSession, *, area_id: int, name: str, scopes: list[str]
) -> tuple[ApiKey, str]:
    """Create a key for the area; returns (row, full_token). Token shown ONCE (D-01)."""
    scopes_str = _validate_scopes(scopes)
    key_id = _new_key_id()
    secret = _new_secret()
    api_key = ApiKey(
        area_id=area_id,
        key_id=key_id,
        secret_hash=hash_password(secret),
        name=name,
        scopes=scopes_str,
    )
    session.add(api_key)
    await session.flush()
    # No secret in the log — only ids (TH-09 / A09).
    logger.info("api_key.created", area_id=area_id, api_key_id=api_key.id, key_id=key_id)
    return api_key, compose_token(key_id, secret)


async def list_api_keys(
    session: AsyncSession, *, area_id: int, limit: int, offset: int
) -> tuple[list[ApiKey], int]:
    """List the area's keys + total (screen 22)."""
    items = await repo.list_for_area(session, area_id=area_id, limit=limit, offset=offset)
    total = await repo.count_for_area(session, area_id=area_id)
    return items, total


async def revoke_api_key(session: AsyncSession, *, area_id: int, key_pk: int) -> ApiKey:
    """Soft-revoke a key owned by THIS area (404 cross-area — TH-03 / D-09)."""
    api_key = await repo.get_for_area(session, area_id=area_id, key_pk=key_pk)
    if api_key is None:
        # No existence leak across areas — 404, not 403.
        raise NotFoundError("Chave de API não encontrada.")
    if api_key.revoked_at is None:
        api_key.revoked_at = datetime.now(UTC)  # AWARE — TD-010
        await session.flush()
    # Invalidate the auth cache so the revoke propagates < 1min (D-09).
    invalidate_api_key_cache(api_key.key_id)
    logger.info("api_key.revoked", area_id=area_id, api_key_id=api_key.id, key_id=api_key.key_id)
    return api_key
