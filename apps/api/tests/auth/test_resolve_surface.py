"""resolve_surface() — post-login surface routing (R0.4).

Validates that the right SPA surface is resolved for each user binding, in the
documented priority: platform admin > area admin > courier > merchant > none.
Runs against the in-memory SQLite (Layer 2) — no network.
"""

from __future__ import annotations

import pytest
from app.areas.models import Area, AreaAdmin
from app.auth.models import User
from app.auth.service import resolve_surface
from app.core.security import hash_password
from app.couriers.models import Courier
from app.merchants.models import Merchant, MerchantUser
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.asyncio


async def _user(s: AsyncSession, email: str, *, role: str = "user") -> User:
    u = User(
        email=email,
        name="Test",
        phone="+5522999990000",
        password_hash=hash_password("correct-horse-staple-10"),
        platform_role=role,
    )
    s.add(u)
    await s.flush()
    return u


async def _area(s: AsyncSession, codename: str) -> Area:
    a = Area(codename=codename, name=codename.title(), config={})
    s.add(a)
    await s.flush()
    return a


async def test_platform_admin_resolves_to_plataforma(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        user = await _user(s, "p@example.com", role="admin_plataforma")
        await s.commit()
        me = await resolve_surface(s, user)
    assert me.surface == "plataforma"
    assert me.area_id is None


async def test_area_admin_resolves_to_admin_with_area(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area = await _area(s, "padua")
        user = await _user(s, "admin@example.com")
        s.add(AreaAdmin(area_id=area.id, user_id=user.id, role="owner"))
        await s.commit()
        me = await resolve_surface(s, user)
    assert me.surface == "admin"
    assert me.area_id == area.id


async def test_courier_resolves_to_entregador(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area = await _area(s, "padua")
        user = await _user(s, "courier@example.com")
        courier = Courier(
            area_id=area.id,
            user_id=user.id,
            cpf="39053344705",
            full_name="João Entregador",
            phone_e164="+5522999990000",
            email="courier@example.com",
            kyc_level="completa",
            status="active",
            vehicle_type="moto",
            vehicle_plate="ABC1D23",
        )
        s.add(courier)
        await s.commit()
        await s.refresh(courier)
        me = await resolve_surface(s, user)
    assert me.surface == "entregador"
    assert me.area_id == area.id
    assert me.courier_id == courier.id
    assert me.status == "active"


async def test_merchant_user_resolves_to_loja(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area = await _area(s, "padua")
        user = await _user(s, "loja@example.com")
        merchant = Merchant(
            area_id=area.id,
            account_type="cnpj",
            document="11222333000181",
            trade_name="Loja do Bairro",
            category="restaurante",
            phone_e164="+5522999991111",
            email="loja@example.com",
            status="active",
        )
        s.add(merchant)
        await s.flush()
        s.add(MerchantUser(merchant_id=merchant.id, user_id=user.id, role="owner"))
        await s.commit()
        me = await resolve_surface(s, user)
    assert me.surface == "loja"
    assert me.area_id == area.id
    assert me.merchant_id == merchant.id
    assert me.status == "active"


async def test_unbound_user_resolves_to_none(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        user = await _user(s, "nobody@example.com")
        await s.commit()
        me = await resolve_surface(s, user)
    assert me.surface == "none"
