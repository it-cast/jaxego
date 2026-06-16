"""Area-admin courier list / KYC queue (F2.0 / MR-2).

list_area_couriers: area-scoped (TH-09), optional status filter (KYC queue), and
the platform-admin cross-area bypass (area_id=None). In-memory SQLite.
"""

from __future__ import annotations

import pytest
from app.areas.models import Area
from app.auth.models import User
from app.core.security import hash_password
from app.couriers.models import Courier
from app.couriers.service import list_area_couriers
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.asyncio

_CPFS = ["39053344705", "11144477735", "15350946056", "40443692050"]


async def _courier(s: AsyncSession, area_id: int, idx: int, status: str) -> Courier:
    user = User(
        email=f"c{idx}@example.com",
        name="Entregador",
        phone="+5522999990000",
        password_hash=hash_password("correct-horse-staple-10"),
        platform_role="user",
    )
    s.add(user)
    await s.flush()
    courier = Courier(
        area_id=area_id,
        user_id=user.id,
        cpf=_CPFS[idx],
        full_name=f"Entregador {idx}",
        phone_e164="+5522999990000",
        email=f"c{idx}@example.com",
        kyc_level="completa",
        status=status,
        vehicle_type="moto",
        vehicle_plate="ABC1D23",
    )
    s.add(courier)
    await s.flush()
    return courier


async def test_list_scoped_filtered_and_bypass(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area_a = Area(codename="padua", name="Pádua", config={})
        area_b = Area(codename="itaocara", name="Itaocara", config={})
        s.add_all([area_a, area_b])
        await s.flush()
        await _courier(s, area_a.id, 0, "pending_kyc")
        await _courier(s, area_a.id, 1, "pending_kyc")
        await _courier(s, area_a.id, 2, "active")
        await _courier(s, area_b.id, 3, "pending_kyc")
        await s.commit()

        _, total_a = await list_area_couriers(s, area_id=area_a.id)
        assert total_a == 3

        _, pending_a = await list_area_couriers(s, area_id=area_a.id, status="pending_kyc")
        assert pending_a == 2

        _, total_b = await list_area_couriers(s, area_id=area_b.id)
        assert total_b == 1

        # Platform admin (area_id=None) sees every area.
        _, total_all = await list_area_couriers(s, area_id=None)
        assert total_all == 4
