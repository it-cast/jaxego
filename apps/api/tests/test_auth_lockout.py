"""Lockout 5/15min (T-13, REQ-005 — ROADMAP acceptance criterion).

The 6th login attempt within the window returns 423 (account locked). Datetimes
in the lock window are aware UTC (TD-010): the comparison never raises a
naive/aware TypeError.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.helpers import Seed


@pytest.mark.asyncio
async def test_sixth_attempt_locks_account_423(auth_client: AsyncClient, seed: Seed) -> None:
    email = seed.admin_a.email
    # 5 wrong attempts: each 401 (invalid credentials), accumulating failures.
    for _ in range(5):
        r = await auth_client.post(
            "/v1/auth/login", json={"email": email, "password": "wrong-password-10"}
        )
        assert r.status_code in (401, 423)
    # The 6th attempt (now over the threshold) is locked -> 423.
    locked = await auth_client.post(
        "/v1/auth/login", json={"email": email, "password": "wrong-password-10"}
    )
    assert locked.status_code == 423
    assert locked.json()["error"]["code"] == "account_locked"


@pytest.mark.asyncio
async def test_locked_account_blocks_even_correct_password(
    auth_client: AsyncClient, seed: Seed
) -> None:
    email = seed.admin_a.email
    for _ in range(5):
        await auth_client.post(
            "/v1/auth/login", json={"email": email, "password": "wrong-password-10"}
        )
    # Even the correct password is rejected with 423 while locked.
    r = await auth_client.post("/v1/auth/login", json={"email": email, "password": seed.password})
    assert r.status_code == 423
