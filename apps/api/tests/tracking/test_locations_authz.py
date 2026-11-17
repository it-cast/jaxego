"""Barreira de IDOR do entregador (TH-5 / DEC-002): só o dono acessa a entrega.

`get_delivery_for_courier` é exercitada direto: o entregador B na entrega do entregador A → 404
(NotFoundError, nunca 403). Desde 71bc973 não há mais ingestão de amostras de localização
(`app.tracking.locations` saiu; `delivery_locations` virou o log append-only das ações do
entregador, escrito só por `app.tracking.service.log_courier_action`), então os testes de
janela/gravação da amostra saíram junto. Seed próprio: dois entregadores + uma entrega ACEITA do
primeiro.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.core.exceptions import NotFoundError
from app.core.security import hash_password
from app.couriers.models import Courier
from app.deliveries.models import Delivery
from app.dispatch.dependencies import CourierScope
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from app.proofs.service import get_delivery_for_courier
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.helpers import make_team

NEAR_LAT, NEAR_LNG = -21.5405, -42.1800


@dataclass
class LocSeed:
    area_id: int
    delivery_id: int
    courier_id: int
    courier_user_id: int
    other_courier_id: int


@pytest_asyncio.fixture
async def loc_seed(session_factory: async_sessionmaker[AsyncSession]) -> LocSeed:
    async with session_factory() as s:
        area = Area(codename="padua", name="Pádua", config={})
        s.add(area)
        await s.flush()
        nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
        s.add(nbhd)
        await s.flush()
        c1 = Courier(
            area_id=area.id,
            team_id=(await make_team(s, area_id=area.id)).id,
            password_hash=hash_password("correct-horse-staple-10"),
            cpf="39053344705",
            full_name="C1",
            phone_e164="+5522999990000",
            email="c1@example.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
            is_online=True,
        )
        c2 = Courier(
            area_id=area.id,
            team_id=(await make_team(s, area_id=area.id)).id,
            password_hash=hash_password("correct-horse-staple-10"),
            cpf="52998224725",
            full_name="C2",
            phone_e164="+5522999990001",
            email="c2@example.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
            is_online=True,
        )
        s.add_all([c1, c2])
        await s.flush()
        merchant = Merchant(
            area_id=area.id,
            account_type="cnpj",
            document="11222333000181",
            trade_name="Loja",
            category="restaurante",
            phone_e164="+5522999991111",
            email="loja@example.com",
            status="active",
        )
        s.add(merchant)
        await s.flush()
        delivery = Delivery(
            area_id=area.id,
            merchant_id=merchant.id,
            courier_id=c1.id,
            recipient_id=None,
            state="ACEITA",
            dispatch_mode="direct",
            payment_method="direct",
            proof_method="photo",
            pickup_address="Rua A, 1",
            dropoff_address="Rua B, 2",
            dropoff_neighborhood_id=nbhd.id,
            fee_cents=0,
            items_quantity=1,
            public_token="LOCTOKEN000000000000000001",
            origin="manual",
        )
        s.add(delivery)
        await s.flush()
        await s.commit()
        return LocSeed(
            area_id=area.id,
            delivery_id=delivery.id,
            courier_id=c1.id,
            courier_user_id=c1.id,  # o entregador é a conta (ator) desde dd23333
            other_courier_id=c2.id,
        )


def _scope(seed: LocSeed, courier_id: int) -> CourierScope:
    return CourierScope(area_id=seed.area_id, courier_id=courier_id, user_id=seed.courier_user_id)


@pytest.mark.asyncio
async def test_non_owner_gets_404_not_403(
    session_factory: async_sessionmaker[AsyncSession], loc_seed: LocSeed
) -> None:
    """Entregador B na entrega do entregador A → 404 (IDOR fechado)."""
    async with session_factory() as s:
        with pytest.raises(NotFoundError):
            await get_delivery_for_courier(
                s, delivery_id=loc_seed.delivery_id, courier_id=loc_seed.other_courier_id
            )


@pytest.mark.asyncio
async def test_get_delivery_for_courier_owner_ok(
    session_factory: async_sessionmaker[AsyncSession], loc_seed: LocSeed
) -> None:
    async with session_factory() as s:
        delivery = await get_delivery_for_courier(
            s, delivery_id=loc_seed.delivery_id, courier_id=loc_seed.courier_id
        )
        assert delivery.id == loc_seed.delivery_id
