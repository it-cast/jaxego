"""Fixtures for suspension/appeal tests (Phase 13). Active courier in area A."""

from __future__ import annotations

from dataclasses import dataclass

import pytest_asyncio
from app.couriers.models import Courier
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers import Seed


@dataclass
class SuspensionWorld:
    area_id: int
    courier_id: int
    admin_id: int


@pytest_asyncio.fixture
async def suspension_world(db_session: AsyncSession, seed: Seed) -> SuspensionWorld:
    courier = Courier(
        area_id=seed.area_a.id,
        user_id=seed.admin_a.id,
        cpf="39053344705",
        full_name="João Entregador",
        phone_e164="+5522999990000",
        email="courier@example.com",
        kyc_level="simples",
        status="active",
        vehicle_type="moto",
    )
    db_session.add(courier)
    await db_session.flush()
    await db_session.commit()
    return SuspensionWorld(
        area_id=seed.area_a.id, courier_id=courier.id, admin_id=seed.admin_a.id
    )
