"""Fixtures for the courier/KYC tests (Phase 5).

Everything runs against the SQLite in-memory DB (Layer 2 of tests/conftest.py)
and the STUB adapters — NEVER the network and NEVER real B2 (Pitfall 1 / Gate 5).
`storage_stub` is the filesystem-temp StoragePort the documents flow uses.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.auth.models import User
from app.core.security import hash_password
from app.couriers.models import Courier
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@pytest.fixture
def storage_stub(tmp_path) -> Iterator[object]:
    """A StoragePort backed by a temp filesystem (no network, no real B2)."""
    # Imported lazily so tests not needing storage do not require the adapter.
    from app.integrations.storage_stub import StorageStubAdapter

    yield StorageStubAdapter(root=tmp_path / "b2-stub")


@pytest_asyncio.fixture
async def courier_seed(
    session_factory: async_sessionmaker[AsyncSession],
) -> dict[str, object]:
    """Seed two areas + a user, returning ids for the courier tests."""
    async with session_factory() as s:
        area_a = Area(codename="padua", name="Pádua", config={"kyc_level": "completa"})
        area_b = Area(codename="itaocara", name="Itaocara", config={"kyc_level": "simples"})
        s.add_all([area_a, area_b])
        await s.flush()
        user = User(
            email="entregador@example.com",
            name="João Entregador",
            phone="+5522999990000",
            password_hash=hash_password("correct-horse-staple-10"),
            platform_role="user",
        )
        s.add(user)
        await s.commit()
        await s.refresh(area_a)
        await s.refresh(area_b)
        await s.refresh(user)
        return {"area_a_id": area_a.id, "area_b_id": area_b.id, "user_id": user.id}


async def make_courier(
    session: AsyncSession,
    *,
    area_id: int,
    user_id: int,
    cpf: str = "39053344705",
    status: str = "pending_kyc",
    kyc_level: str = "completa",
) -> Courier:
    """Insert a minimal courier row and return it."""
    courier = Courier(
        area_id=area_id,
        user_id=user_id,
        cpf=cpf,
        full_name="João Entregador",
        phone_e164="+5522999990000",
        email="entregador@example.com",
        kyc_level=kyc_level,
        status=status,
        vehicle_type="moto",
        vehicle_plate="ABC1D23",
    )
    session.add(courier)
    await session.flush()
    return courier
