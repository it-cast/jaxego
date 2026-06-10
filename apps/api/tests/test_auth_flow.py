"""Auth flow + anti-enumeration (T-14, REQ-005/REQ-006).

Covers: login happy path (access + refresh); refresh rotation; reuse of a spent
refresh revokes the family; generic message + ~constant time for unknown user vs
wrong password; login events carry no PII.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.helpers import Seed, login


@pytest.mark.asyncio
async def test_login_happy_path_returns_access_and_refresh(
    auth_client: AsyncClient, seed: Seed
) -> None:
    body = await login(auth_client, seed.admin_a.email, seed.password)
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 15 * 60


@pytest.mark.asyncio
async def test_refresh_rotates_token(auth_client: AsyncClient, seed: Seed) -> None:
    first = await login(auth_client, seed.admin_a.email, seed.password)
    resp = await auth_client.post(
        "/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    )
    assert resp.status_code == 200
    rotated = resp.json()
    assert rotated["refresh_token"] != first["refresh_token"]  # rotated


@pytest.mark.asyncio
async def test_refresh_reuse_revokes_family(auth_client: AsyncClient, seed: Seed) -> None:
    first = await login(auth_client, seed.admin_a.email, seed.password)
    old = first["refresh_token"]
    # First rotation succeeds.
    r1 = await auth_client.post("/v1/auth/refresh", json={"refresh_token": old})
    assert r1.status_code == 200
    new = r1.json()["refresh_token"]
    # Reusing the spent (old) token => reuse detected => 401 + family revoked.
    r2 = await auth_client.post("/v1/auth/refresh", json={"refresh_token": old})
    assert r2.status_code == 401
    assert r2.json()["error"]["code"] == "refresh_reuse_detected"
    # The previously-issued new token is now revoked too (family revoked).
    r3 = await auth_client.post("/v1/auth/refresh", json={"refresh_token": new})
    assert r3.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh(auth_client: AsyncClient, seed: Seed) -> None:
    body = await login(auth_client, seed.admin_a.email, seed.password)
    out = await auth_client.post("/v1/auth/logout", json={"refresh_token": body["refresh_token"]})
    assert out.status_code == 204
    again = await auth_client.post(
        "/v1/auth/refresh", json={"refresh_token": body["refresh_token"]}
    )
    assert again.status_code == 401


# --- anti-enumeration (RN-011 / REQ-006) ---


@pytest.mark.asyncio
async def test_unknown_user_and_wrong_password_same_message(
    auth_client: AsyncClient, seed: Seed
) -> None:
    unknown = await auth_client.post(
        "/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever-10c"}
    )
    wrong = await auth_client.post(
        "/v1/auth/login", json={"email": seed.admin_a.email, "password": "wrong-password-10"}
    )
    assert unknown.status_code == 401
    assert wrong.status_code == 401
    # Identical generic message and code — does not reveal which is which.
    assert unknown.json()["error"]["message"] == wrong.json()["error"]["message"]
    assert unknown.json()["error"]["code"] == wrong.json()["error"]["code"]
    assert unknown.json()["error"]["message"] == "Credenciais inválidas."


@pytest.mark.asyncio
async def test_login_logs_carry_no_pii(
    auth_client: AsyncClient, seed: Seed, capsys: pytest.CaptureFixture[str]
) -> None:
    await auth_client.post(
        "/v1/auth/login", json={"email": seed.admin_a.email, "password": "wrong-password-10"}
    )
    out = capsys.readouterr().out
    # Login events must not leak email/password into structured logs.
    assert seed.admin_a.email not in out
    assert "wrong-password-10" not in out
