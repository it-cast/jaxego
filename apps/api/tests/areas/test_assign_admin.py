"""Designar admin de área (F3.3 / MR-3)."""

from __future__ import annotations

import pytest
from app.areas.models import Area, AreaAdmin
from app.areas.service import AdminUserNotFoundError, assign_area_admin
from app.core.security import hash_password
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.asyncio


async def _area(s: AsyncSession) -> Area:
    a = Area(codename="padua", name="Pádua", config={})
    s.add(a)
    await s.flush()
    return a


async def _user(s: AsyncSession, email: str, area_id: int) -> AreaAdmin:
    """Conta de admin (desde dd23333 não há `users`): assign_area_admin move a conta para a área."""
    u = AreaAdmin(
        area_id=area_id,
        name="Gestor",
        email=email,
        password_hash=hash_password("correct-horse-staple-10"),
        role="viewer",
    )
    s.add(u)
    await s.flush()
    return u


async def test_assign_creates_then_updates_role(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area = await _area(s)
        await _user(s, "gestor@example.com", area.id)
        await s.commit()

        membership, email = await assign_area_admin(
            s, area_id=area.id, user_email="gestor@example.com", role="manager"
        )
        assert email == "gestor@example.com"
        assert membership.role == "manager"

        # Re-assign updates the role (no duplicate row — UNIQUE area_id+user_id).
        again, _ = await assign_area_admin(
            s, area_id=area.id, user_email="gestor@example.com", role="owner"
        )
        assert again.id == membership.id
        assert again.role == "owner"
        rows = (
            (await s.execute(select(AreaAdmin).where(AreaAdmin.area_id == area.id))).scalars().all()
        )
        assert len(rows) == 1


async def test_assign_unknown_email_raises(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area = await _area(s)
        await s.commit()
        with pytest.raises(AdminUserNotFoundError):
            await assign_area_admin(
                s, area_id=area.id, user_email="ninguem@example.com", role="manager"
            )
