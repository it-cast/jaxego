"""resolve_surface_for() — superfície pós-login por tipo de conta (R0.4).

Desde dd23333 não há tabela `users` nem prioridade entre vínculos: cada tipo de conta
(entregador, loja,
equipe, admin da área, admin da plataforma) é uma tabela própria e cai SEMPRE na sua superfície.
Roda no SQLite em memória (Layer 2) — sem rede.
"""

from __future__ import annotations

import pytest
from app.areas.models import Area, AreaAdmin
from app.auth.models import PlatformAdmin
from app.auth.principals import build_actor
from app.auth.service import resolve_surface_for
from app.core.security import hash_password
from app.couriers.models import Courier
from app.merchants.models import Merchant
from app.teams.models import Team
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.asyncio

SENHA = hash_password("correct-horse-staple-10")


async def _area(s: AsyncSession) -> Area:
    a = Area(codename="padua", name="Pádua", config={})
    s.add(a)
    await s.flush()
    return a


async def test_platform_admin_resolves_to_plataforma(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        admin = PlatformAdmin(email="p@example.com", name="Plataforma", password_hash=SENHA)
        s.add(admin)
        await s.commit()
        me = resolve_surface_for(build_actor("platform_admin", admin))
    assert me.surface == "plataforma"
    assert me.area_id is None


async def test_area_admin_resolves_to_admin_with_area(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area = await _area(s)
        admin = AreaAdmin(
            area_id=area.id,
            name="Admin",
            email="admin@example.com",
            password_hash=SENHA,
            role="owner",
        )
        s.add(admin)
        await s.commit()
        me = resolve_surface_for(build_actor("area_admin", admin))
    assert me.surface == "admin"
    assert me.area_id == area.id


async def test_courier_resolves_to_entregador(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area = await _area(s)
        team = Team(area_id=area.id, name="Equipe", email="equipe@example.com", password_hash=SENHA)
        s.add(team)
        await s.flush()
        courier = Courier(
            area_id=area.id,
            team_id=team.id,
            password_hash=SENHA,
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
        me = resolve_surface_for(build_actor("courier", courier))
    assert me.surface == "entregador"
    assert me.area_id == area.id
    assert me.courier_id == courier.id
    assert me.status == "active"


async def test_merchant_resolves_to_loja(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as s:
        area = await _area(s)
        merchant = Merchant(
            area_id=area.id,
            account_type="cnpj",
            document="11222333000181",
            trade_name="Loja do Bairro",
            category="restaurante",
            phone_e164="+5522999991111",
            email="loja@example.com",
            password_hash=SENHA,
            status="active",
        )
        s.add(merchant)
        await s.commit()
        me = resolve_surface_for(build_actor("merchant", merchant))
    assert me.surface == "loja"
    assert me.area_id == area.id
    assert me.merchant_id == merchant.id
    assert me.trade_name == "Loja do Bairro"


async def test_team_resolves_to_equipe(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as s:
        area = await _area(s)
        team = Team(area_id=area.id, name="Equipe", email="equipe@example.com", password_hash=SENHA)
        s.add(team)
        await s.commit()
        me = resolve_surface_for(build_actor("team", team))
    assert me.surface == "equipe"
    assert me.area_id == area.id
    assert me.team_id == team.id
