"""`api_key_scope` — resolve a public-API request to an (area_id, scopes) scope.

This is the auth chokepoint for the public API (mirrors `MerchantScopeDep`). The
flow (TH-01 / A07):

  1. parse the header (`Authorization: Bearer jxg_...` OR `X-API-Key: jxg_...`)
  2. split the prefix → `key_id` (public) + `secret` (credential)
  3. fetch the row by `key_id`; if missing/revoked, run a DUMMY argon2id verify so
     the response time does NOT reveal existence (anti-enumeration, constant latency)
  4. verify the secret against `secret_hash` with argon2id (timing-safe by design)
  5. inject `(area_id, scopes)`

A short in-process cache (TTL 30s) avoids an argon2id verify on every request; it
is INVALIDATED on revoke (`invalidate_api_key_cache`) so a revoked key stops
working in < 1min (D-09 / RN-020). EVERY failure path raises the SAME
`ApiKeyAuthError` (401, identical body) — never distinguishing "no key" from
"wrong secret" from "revoked" (anti-enumeration). The secret is NEVER logged (TH-09).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

import structlog
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_keys import repo
from app.core.exceptions import AppError
from app.core.security import verify_dummy, verify_password
from app.db.session import get_session

logger = structlog.get_logger("api_keys.auth")

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Cache TTL — bounded so a revoke propagates in < 1min even without explicit
# invalidation; the revoke path ALSO invalidates synchronously (D-09).
_CACHE_TTL = timedelta(seconds=30)


class ApiKeyAuthError(AppError):
    """Invalid / missing / revoked API key — ALWAYS the same 401 (anti-enumeration)."""

    status_code = 401
    code = "api_key_invalid"

    def __init__(self) -> None:
        # Identical message on every failure path — never reveals which check failed.
        super().__init__("Chave de API inválida.")


@dataclass(frozen=True)
class ApiKeyScope:
    """The resolved (area_id, scopes) for an authenticated public-API request."""

    area_id: int
    api_key_id: int
    key_id: str
    scopes: frozenset[str]

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes


# --- In-process verified-secret cache (TTL 30s; invalidated on revoke) ---
@dataclass
class _CacheEntry:
    scope: ApiKeyScope
    secret: str  # the verified plaintext (kept only in-memory, never persisted/logged)
    expires_at: datetime


_cache: dict[str, _CacheEntry] = {}


def invalidate_api_key_cache(key_id: str | None = None) -> None:
    """Drop a cached key (on revoke) or the whole cache (key_id=None)."""
    if key_id is None:
        _cache.clear()
    else:
        _cache.pop(key_id, None)


def _parse_header(request: Request) -> str | None:
    """Return the raw `jxg_...` token from Authorization or X-API-Key, or None."""
    auth = request.headers.get("Authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() == "bearer" and token:
        return token.strip()
    x_api_key = request.headers.get("X-API-Key", "")
    if x_api_key:
        return x_api_key.strip()
    return None


def _split_token(token: str) -> tuple[str, str] | None:
    """Split `jxg_<key_id>_<secret>` → (key_id, secret); None if malformed."""
    parts = token.split("_", 2)
    if len(parts) != 3 or parts[0] != "jxg" or not parts[1] or not parts[2]:
        return None
    return parts[1], parts[2]


def _scope_from_key(key) -> ApiKeyScope:
    return ApiKeyScope(
        area_id=key.area_id,
        api_key_id=key.id,
        key_id=key.key_id,
        scopes=frozenset(key.scopes.split()),
    )


async def api_key_scope(request: Request, session: SessionDep) -> ApiKeyScope:
    """Resolve the request's API key to an (area_id, scopes) scope, or stable 401.

    Constant-time on every failure (a dummy argon2id verify is run when the key is
    missing/revoked) so the 401 latency never reveals whether the key exists.
    """
    token = _parse_header(request)
    if token is None:
        # Spend a verify to keep latency comparable even on a missing header.
        verify_dummy("no-token")
        raise ApiKeyAuthError()

    split = _split_token(token)
    if split is None:
        verify_dummy("malformed")
        raise ApiKeyAuthError()
    key_id, secret = split

    now = datetime.now(UTC)

    # Fast path: a recently-verified secret for this key_id (TTL 30s).
    cached = _cache.get(key_id)
    if cached is not None and cached.expires_at > now and cached.secret == secret:
        return cached.scope

    api_key = await repo.get_by_key_id(session, key_id=key_id)
    if api_key is None or api_key.revoked_at is not None:
        # Constant-time: verify against a dummy hash so a missing/revoked key costs
        # the same as a real verify (anti-enumeration). NEVER log the secret (TH-09).
        verify_dummy(secret)
        raise ApiKeyAuthError()

    ok, _ = verify_password(api_key.secret_hash, secret)
    if not ok:
        raise ApiKeyAuthError()

    scope = _scope_from_key(api_key)
    _cache[key_id] = _CacheEntry(scope=scope, secret=secret, expires_at=now + _CACHE_TTL)
    return scope


ApiKeyScopeDep = Annotated[ApiKeyScope, Depends(api_key_scope)]


def require_scope(scope: str):
    """Dependency factory: require a specific scope on the resolved API key (403)."""

    async def _dep(api_scope: ApiKeyScopeDep) -> ApiKeyScope:
        if not api_scope.has_scope(scope):
            logger.warning("api_key_missing_scope", api_key_id=api_scope.api_key_id, scope=scope)
            raise ApiKeyForbiddenError()
        return api_scope

    return _dep


class ApiKeyForbiddenError(AppError):
    """Authenticated key without the required scope (403)."""

    status_code = 403
    code = "api_key_forbidden"

    def __init__(self) -> None:
        super().__init__("A chave de API não tem permissão para esta operação.")
