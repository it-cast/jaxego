"""API-key auth dependency (T-03 / TH-01) — stable 401, revoke <1min, IDOR scope.

Covers:
- a valid key resolves to its area scope;
- a missing / malformed / wrong-secret / revoked key ALL return the SAME 401 body
  (anti-enumeration — never reveals which check failed);
- a revoked key stops working immediately (cache invalidated on revoke — D-09);
- the resolved scope is the key's area (cross-area write is impossible by construction).
"""

from __future__ import annotations

import pytest
from app.api_keys import service as key_service
from app.api_keys.dependencies import (
    ApiKeyAuthError,
    api_key_scope,
    invalidate_api_key_cache,
)


class _FakeRequest:
    """Minimal request stub carrying just the headers the dependency reads."""

    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


async def _resolve(token: str | None, session, *, scheme: str = "bearer"):
    headers: dict[str, str] = {}
    if token is not None:
        if scheme == "bearer":
            headers["Authorization"] = f"Bearer {token}"
        else:
            headers["X-API-Key"] = token
    return await api_key_scope(_FakeRequest(headers), session)


@pytest.mark.asyncio
async def test_valid_key_resolves_area_scope(public_api_seed, session_factory) -> None:
    async with session_factory() as s:
        scope = await _resolve(public_api_seed.token, s)
    assert scope.area_id == public_api_seed.area_a_id
    assert scope.api_key_id == public_api_seed.api_key_id
    assert scope.has_scope("deliveries:write")


@pytest.mark.asyncio
async def test_x_api_key_header_also_accepted(public_api_seed, session_factory) -> None:
    async with session_factory() as s:
        scope = await _resolve(public_api_seed.token, s, scheme="x-api-key")
    assert scope.area_id == public_api_seed.area_a_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad",
    [
        None,  # missing header
        "garbage",  # not jxg_ form
        "jxg_only",  # malformed (no secret)
        "jxg_unknownkey_somesecret",  # unknown key_id
    ],
)
async def test_invalid_keys_all_raise_same_401(bad, public_api_seed, session_factory) -> None:
    async with session_factory() as s:
        with pytest.raises(ApiKeyAuthError) as exc:
            await _resolve(bad, s)
    assert exc.value.status_code == 401
    assert exc.value.code == "api_key_invalid"
    assert exc.value.message == "Chave de API inválida."


@pytest.mark.asyncio
async def test_wrong_secret_same_401_as_unknown_key(public_api_seed, session_factory) -> None:
    # A real key_id with the wrong secret must look identical to an unknown key (anti-enum).
    real_key_id = public_api_seed.key_id
    forged = f"jxg_{real_key_id}_wrong-secret-here"
    async with session_factory() as s:
        with pytest.raises(ApiKeyAuthError) as exc:
            await _resolve(forged, s)
    assert exc.value.code == "api_key_invalid"


@pytest.mark.asyncio
async def test_revoke_is_effective_immediately(public_api_seed, session_factory) -> None:
    # The key works, then we revoke it and it must stop working at once (cache invalidated).
    async with session_factory() as s:
        scope = await _resolve(public_api_seed.token, s)
        assert scope.area_id == public_api_seed.area_a_id
        await key_service.revoke_api_key(
            s, area_id=public_api_seed.area_a_id, key_pk=public_api_seed.api_key_id
        )
        await s.commit()

    async with session_factory() as s:
        with pytest.raises(ApiKeyAuthError):
            await _resolve(public_api_seed.token, s)


@pytest.mark.asyncio
async def test_revoke_cross_area_is_404(public_api_seed, session_factory) -> None:
    # Area B cannot revoke Area A's key — 404, no existence leak (TH-03).
    from app.core.exceptions import NotFoundError

    async with session_factory() as s:
        with pytest.raises(NotFoundError):
            await key_service.revoke_api_key(
                s, area_id=public_api_seed.area_b_id, key_pk=public_api_seed.api_key_id
            )


@pytest.mark.asyncio
async def test_secret_is_never_persisted_plaintext(public_api_seed, session_factory) -> None:
    from app.api_keys import repo

    async with session_factory() as s:
        key = await repo.get_by_key_id(s, key_id=public_api_seed.key_id)
    # The DB holds an argon2id hash, never the plaintext secret (TH-01/TH-09).
    assert key.secret_hash.startswith("$argon2")
    assert public_api_seed.token.split("_", 2)[2] not in key.secret_hash


def teardown_function() -> None:
    invalidate_api_key_cache()
