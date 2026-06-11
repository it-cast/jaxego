"""Fixtures for the invoices tests (Phase 15 — REQ-037 / F-03 E5).

Builds a minimal world against the SQLite in-memory DB (Layer 2 of tests/conftest.py):
an area, a store owner + Merchant + active Free subscription, and a helper to insert
DIRECT deliveries with a recorded platform fee in a chosen month. The invoice service
aggregates these into a `platform_invoices` row (1/loja/competência — D-01).

No network: invoice payment uses the `PaymentStubAdapter` (D-09).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import count

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.auth.models import User
from app.core.security import hash_password
from app.deliveries.models import Delivery
from app.merchants.models import Merchant, MerchantSubscription, MerchantUser
from app.neighborhoods.models import Neighborhood
from app.plans.models import SubscriptionPlan
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PASSWORD = "correct-horse-staple-10"
_token_seq = count(1)


@dataclass
class InvoiceSeed:
    area_id: int
    merchant_id: int
    owner_user_id: int
    plan_fee_cents: int
    dropoff_nbhd_id: int


@pytest.fixture
def payment_stub():
    """Deterministic Stub adapter (no network). Default scenario: approved."""
    from app.payments.safe2pay_stub import PaymentStubAdapter

    return PaymentStubAdapter(scenario="approved")


@pytest_asyncio.fixture
async def invoice_seed(session_factory: async_sessionmaker[AsyncSession]) -> InvoiceSeed:
    """Area + store + active Free subscription (fee 200 cents)."""
    async with session_factory() as s:
        area = Area(codename="padua", name="Pádua", config={})
        s.add(area)
        await s.flush()

        owner = User(
            email="loja@example.com",
            name="Loja Dona",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        s.add(owner)
        await s.flush()

        merchant = Merchant(
            area_id=area.id,
            account_type="cnpj",
            document="12345678000190",
            trade_name="Padaria do João",
            category="alimentacao",
            phone_e164="+5522999990001",
            email="loja@example.com",
            status="active",
        )
        s.add(merchant)
        await s.flush()
        s.add(MerchantUser(merchant_id=merchant.id, user_id=owner.id, role="owner"))

        plan = SubscriptionPlan(
            code="free",
            name="Free",
            price_cents=0,
            deliveries_per_month=30,
            fee_cents=200,
            is_free=True,
            is_unlimited=False,
            sort_order=0,
        )
        s.add(plan)
        await s.flush()
        s.add(
            MerchantSubscription(
                area_id=area.id,
                merchant_id=merchant.id,
                plan_id=plan.id,
                status="active",
                billing_status="active",
            )
        )
        dropoff = Neighborhood(area_id=area.id, name="Aeroporto", is_informal=False)
        s.add(dropoff)
        await s.flush()

        await s.commit()
        return InvoiceSeed(
            area_id=area.id,
            merchant_id=merchant.id,
            owner_user_id=owner.id,
            plan_fee_cents=plan.fee_cents,
            dropoff_nbhd_id=dropoff.id,
        )


async def make_direct_delivery(
    session: AsyncSession,
    *,
    area_id: int,
    merchant_id: int,
    dropoff_nbhd_id: int,
    fee_cents: int,
    created_at: datetime,
) -> Delivery:
    """Insert a DIRECT delivery with a recorded platform fee at `created_at` (aware-UTC)."""
    delivery = Delivery(
        area_id=area_id,
        merchant_id=merchant_id,
        courier_id=None,
        recipient_id=None,
        state="ENTREGUE",
        dispatch_mode="direct",
        payment_method="direct",
        proof_method="foto",
        pickup_address="Rua A, 1",
        pickup_neighborhood="Centro",
        dropoff_address="Rua B, 2",
        dropoff_neighborhood_id=dropoff_nbhd_id,
        distance_m=1000,
        estimate_min_cents=1000,
        estimate_max_cents=1000,
        fee_cents=fee_cents,
        items_quantity=1,
        public_token=f"tok{next(_token_seq)}",
        origin="manual",
        created_at=created_at if created_at.tzinfo else created_at.replace(tzinfo=UTC),
    )
    session.add(delivery)
    await session.flush()
    return delivery
