"""Platform-admin endpoints: TOTP gate, cross-area audit, bound filters (T-08 / REQ-046).

Drives real HTTP via `auth_client` (the SQLite-backed app). Asserts:
- a platform admin WITHOUT TOTP enrolled is blocked (403 totp_enrollment_required — TH-01);
- an enrolled platform admin's cross-area read writes an audit_log row (TH-02);
- a bound search filter (`q`) with an injection-shaped value is parametrised, not executed
  (no error, no leak — TH-06).
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from app.audit.models import AuditLog
from app.auth.models import User
from app.core.security import encode_access
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.helpers import Seed, bearer


@pytest_asyncio.fixture
async def enrolled_admin_token(
    session_factory: async_sessionmaker[AsyncSession], seed: Seed
) -> str:
    """Mark the platform admin TOTP-enrolled and mint a cross-area access token."""
    async with session_factory() as s:
        admin = await s.get(User, seed.platform_admin.id)
        admin.totp_enrolled = True
        await s.commit()
    return encode_access(seed.platform_admin.id, area_scope=None, role="admin_plataforma")


@pytest.mark.asyncio
async def test_platform_admin_without_totp_is_blocked(auth_client: AsyncClient, seed: Seed) -> None:
    """A platform admin not yet TOTP-enrolled cannot reach platform routes (TH-01)."""
    token = encode_access(seed.platform_admin.id, area_scope=None, role="admin_plataforma")
    resp = await auth_client.get("/v1/platform/overview", headers=bearer(token))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "totp_enrollment_required"


@pytest.mark.asyncio
async def test_non_platform_admin_forbidden(auth_client: AsyncClient, seed: Seed) -> None:
    """An area admin cannot reach platform routes (TH-04 — privilege escalation)."""
    token = encode_access(seed.admin_a.id, area_scope=seed.area_a.id, role="admin_area")
    resp = await auth_client.get("/v1/platform/overview", headers=bearer(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_overview_audits_cross_area_access(
    auth_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    enrolled_admin_token: str,
) -> None:
    """A cross-area read writes an audit_log row with cross_area_bypass (TH-02)."""
    resp = await auth_client.get("/v1/platform/overview", headers=bearer(enrolled_admin_token))
    assert resp.status_code == 200

    async with session_factory() as s:
        rows = (
            (await s.execute(select(AuditLog).where(AuditLog.action == "platform.area_overview")))
            .scalars()
            .all()
        )
        assert len(rows) >= 1
        assert rows[0].cross_area_bypass is True


@pytest.mark.asyncio
async def test_courier_search_filter_is_bound(
    auth_client: AsyncClient, enrolled_admin_token: str
) -> None:
    """An injection-shaped `q` is parametrised (no 500, no leak) — TH-06."""
    resp = await auth_client.get(
        "/v1/platform/couriers",
        params={"q": "'; DROP TABLE couriers;--"},
        headers=bearer(enrolled_admin_token),
    )
    assert resp.status_code == 200
    assert resp.json() == []  # no courier matches that literal name
