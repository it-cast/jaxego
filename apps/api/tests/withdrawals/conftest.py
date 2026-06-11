"""Fixtures for the withdrawals tests (Phase 15 — REQ-038 / D-04).

Minimal world against the SQLite in-memory DB (Layer 2 of tests/conftest.py): an area, a
courier, and RELEASED escrow ledger holds that form the withdrawable balance. The payout
goes through the `PaymentStubAdapter` (no network — D-09); a `payout_fails` knob drives
the failure-compensation test.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.auth.models import User
from app.core.security import hash_password
from app.couriers.models import Courier
from app.payments.models import EscrowLedger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PASSWORD = "correct-horse-staple-10"


@dataclass
class WithdrawalSeed:
    area_a_id: int
    area_b_id: int
    courier_id: int
    other_courier_id: int


@pytest.fixture
def payment_stub():
    from app.payments.safe2pay_stub import PaymentStubAdapter

    return PaymentStubAdapter(scenario="approved")


@pytest.fixture
def payout_failing_stub():
    from app.payments.safe2pay_stub import PaymentStubAdapter

    return PaymentStubAdapter(scenario="approved", payout_fails=True)


async def _courier(s: AsyncSession, *, area_id: int, email: str, cpf: str) -> Courier:
    user = User(
        email=email,
        name="Courier",
        password_hash=hash_password(PASSWORD),
        platform_role="user",
    )
    s.add(user)
    await s.flush()
    courier = Courier(
        area_id=area_id,
        user_id=user.id,
        cpf=cpf,
        full_name="Courier",
        phone_e164=f"+55229999{cpf[:5]}",
        email=email,
        kyc_level="simples",
        status="active",
        vehicle_type="moto",
        is_online=True,
        max_concurrent=1,
        s2p_recipient_id=f"recip_{cpf[:4]}",
    )
    s.add(courier)
    await s.flush()
    return courier


@pytest_asyncio.fixture
async def withdrawal_seed(session_factory: async_sessionmaker[AsyncSession]) -> WithdrawalSeed:
    """Area A + courier with two RELEASED holds (1000 + 1500 cents = 2500 balance)."""
    async with session_factory() as s:
        area_a = Area(codename="padua", name="Pádua", config={})
        area_b = Area(codename="itaocara", name="Itaocara", config={})
        s.add_all([area_a, area_b])
        await s.flush()

        courier = await _courier(s, area_id=area_a.id, email="c@example.com", cpf="39053344705")
        other = await _courier(
            s, area_id=area_b.id, email="o@example.com", cpf="11144477735"
        )

        # Released balance for the main courier: 1000 + 1500 = 2500 cents.
        for amt, did in ((1000, 101), (1500, 102)):
            s.add(
                EscrowLedger(
                    area_id=area_a.id,
                    delivery_id=did,
                    courier_id=courier.id,
                    amount_cents=amt,
                    state="RELEASED",
                )
            )
        # A still-HELD hold does NOT count toward the balance.
        s.add(
            EscrowLedger(
                area_id=area_a.id,
                delivery_id=103,
                courier_id=courier.id,
                amount_cents=9999,
                state="HELD",
            )
        )
        await s.commit()
        return WithdrawalSeed(
            area_a_id=area_a.id,
            area_b_id=area_b.id,
            courier_id=courier.id,
            other_courier_id=other.id,
        )
