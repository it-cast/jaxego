"""TOTP enrolment + verification (T-13, REQ-005).

Platform admin without TOTP is forced to enrol before accessing a protected
resource; replay of a TOTP code is rejected; enrolment flips the flags on.
"""

from __future__ import annotations

import pyotp
import pytest
from httpx import AsyncClient

from tests.helpers import Seed, bearer, login


@pytest.mark.asyncio
async def test_platform_admin_without_totp_blocked_from_protected(
    auth_client: AsyncClient, seed: Seed
) -> None:
    """A platform admin who has not enrolled TOTP cannot reach /v1/areas."""
    body = await login(auth_client, seed.platform_admin.email, seed.password)
    resp = await auth_client.get("/v1/areas", headers=bearer(body["access_token"]))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "totp_enrollment_required"


@pytest.mark.asyncio
async def test_platform_admin_can_enroll_then_access(auth_client: AsyncClient, seed: Seed) -> None:
    """Enrol endpoint is reachable without TOTP; after verify, access works."""
    body = await login(auth_client, seed.platform_admin.email, seed.password)
    headers = bearer(body["access_token"])

    enroll = await auth_client.post("/v1/auth/totp/enroll", headers=headers)
    assert enroll.status_code == 200
    secret = enroll.json()["secret"]
    assert enroll.json()["provisioning_uri"].startswith("otpauth://totp/")

    code = pyotp.TOTP(secret).now()
    verify = await auth_client.post("/v1/auth/totp/verify", headers=headers, json={"code": code})
    assert verify.status_code == 204

    # The enrolment gate now passes: get_current_user re-reads the user and sees
    # totp_enrolled=True, so the same access token reaches the protected route.
    ok = await auth_client.get("/v1/areas", headers=headers)
    assert ok.status_code == 200


@pytest.mark.asyncio
async def test_totp_replay_rejected_on_login(auth_client: AsyncClient, seed: Seed) -> None:
    """A TOTP code accepted once cannot be reused in the same window."""
    body = await login(auth_client, seed.platform_admin.email, seed.password)
    headers = bearer(body["access_token"])
    enroll = await auth_client.post("/v1/auth/totp/enroll", headers=headers)
    secret = enroll.json()["secret"]
    code = pyotp.TOTP(secret).now()
    await auth_client.post("/v1/auth/totp/verify", headers=headers, json={"code": code})

    # The verify already consumed this window. A login reusing the same code is
    # rejected as a replay.
    replay = await auth_client.post(
        "/v1/auth/login",
        json={"email": seed.platform_admin.email, "password": seed.password, "totp": code},
    )
    assert replay.status_code == 401
    assert replay.json()["error"]["code"] == "totp_required"
