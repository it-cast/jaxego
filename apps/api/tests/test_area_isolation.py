"""Multi-area isolation + audited platform bypass (T-15, REQ-001 — ROADMAP).

Three layers of isolation are exercised:
1. Dependency: `area_scope` raises 403 when a non-platform admin targets an
   area_id != their token scope (D-06 / F-08 E1).
2. Repository: `AreaScopedRepository.list_for_area` never returns another area's
   rows (Pattern 1, WHERE area_id).
3. Endpoint: a platform admin reaching any area succeeds AND writes an
   `audit_log` row with cross_area_bypass=True (RN-001, never silent).
"""

from __future__ import annotations

import pyotp
import pytest
from app.areas.models import AreaAdmin
from app.audit.models import AuditLog
from app.auth.dependencies import ForbiddenError, area_scope
from app.db.repository import AreaScopedRepository
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers import Seed, bearer, login


class _AreaAdminRepo(AreaScopedRepository[AreaAdmin]):
    model = AreaAdmin


# --- Layer 1: dependency raises 403 cross-area ---


@pytest.mark.asyncio
async def test_area_scope_denies_cross_area() -> None:
    """A non-platform admin targeting another area_id gets 403."""

    class _Req:
        class state:  # noqa: N801
            token_area_scope = 1

    class _User:
        id = 10
        platform_role = "user"

    with pytest.raises(ForbiddenError):
        await area_scope(_Req(), _User(), area_id=2)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_area_scope_allows_same_area() -> None:
    class _Req:
        class state:  # noqa: N801
            token_area_scope = 1

    class _User:
        id = 10
        platform_role = "user"

    scope = await area_scope(_Req(), _User(), area_id=1)  # type: ignore[arg-type]
    assert scope == 1


@pytest.mark.asyncio
async def test_platform_admin_scope_is_none() -> None:
    class _Req:
        class state:  # noqa: N801
            token_area_scope = None

    class _User:
        id = 1
        platform_role = "admin_plataforma"

    scope = await area_scope(_Req(), _User(), area_id=2)  # type: ignore[arg-type]
    assert scope is None


# --- Layer 2: repository never leaks across areas ---


@pytest.mark.asyncio
async def test_repository_list_scoped_to_area(db_session: AsyncSession, seed: Seed) -> None:
    repo = _AreaAdminRepo(db_session)
    in_a = await repo.list_for_area(area_id=seed.area_a.id)
    in_b = await repo.list_for_area(area_id=seed.area_b.id)
    assert all(m.area_id == seed.area_a.id for m in in_a)
    assert all(m.area_id == seed.area_b.id for m in in_b)
    # The area-A listing never contains an area-B membership.
    a_ids = {m.id for m in in_a}
    b_ids = {m.id for m in in_b}
    assert a_ids.isdisjoint(b_ids)


@pytest.mark.asyncio
async def test_repository_get_cross_area_returns_none(db_session: AsyncSession, seed: Seed) -> None:
    """Fetching an area-B membership scoped to area A returns None (-> 404)."""
    b_membership = (
        await db_session.execute(select(AreaAdmin).where(AreaAdmin.area_id == seed.area_b.id))
    ).scalar_one()
    repo = _AreaAdminRepo(db_session)
    found = await repo.get_for_area(b_membership.id, area_id=seed.area_a.id)
    assert found is None


# --- Layer 3: platform bypass is audited ---


async def _enrol_platform_admin(client: AsyncClient, seed: Seed) -> dict[str, str]:
    body = await login(client, seed.platform_admin.email, seed.password)
    headers = bearer(body["access_token"])
    enroll = await client.post("/v1/auth/totp/enroll", headers=headers)
    secret = enroll.json()["secret"]
    await client.post(
        "/v1/auth/totp/verify", headers=headers, json={"code": pyotp.TOTP(secret).now()}
    )
    return headers


@pytest.mark.asyncio
async def test_platform_bypass_audited(
    auth_client: AsyncClient, seed: Seed, db_session: AsyncSession
) -> None:
    headers = await _enrol_platform_admin(auth_client, seed)
    # Platform admin reads area B (not "their" area) -> 200.
    resp = await auth_client.get(f"/v1/areas/{seed.area_b.id}", headers=headers)
    assert resp.status_code == 200

    # An audit_log row was written with cross_area_bypass=True for the actor.
    rows = (
        (
            await db_session.execute(
                select(AuditLog).where(
                    AuditLog.cross_area_bypass.is_(True),
                    AuditLog.action == "area.read",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) >= 1
    assert rows[0].actor_user_id == seed.platform_admin.id


@pytest.mark.asyncio
async def test_area_admin_cannot_reach_areas_crud(auth_client: AsyncClient, seed: Seed) -> None:
    """An area admin (not platform) is forbidden from the platform-only CRUD."""
    body = await login(auth_client, seed.admin_a.email, seed.password)
    resp = await auth_client.get(
        f"/v1/areas/{seed.area_b.id}", headers=bearer(body["access_token"])
    )
    assert resp.status_code == 403
