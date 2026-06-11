"""Dispute financial decision + RN-027 block (Phase 15 — REQ-039 / D-03).

T-04: deciding a dispute `procedente` issues a refund/credit via the PaymentPort and
records the adjustment; `improcedente` moves no money. Both are AUDITED.

T-05 (RN-027, controlled clock): 2 `procedente` decisions within 30 days for the same
courier open a 90-day `DisputeBlock`; the block expires at 90d (`expire_blocks`). The
30d window counts (a 3rd, separated procedente outside the window does not stack a 2nd
block while one is active — idempotent). Direct confirmation is rejected while blocked.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.auth.models import User
from app.core.security import hash_password
from app.couriers.models import Courier
from app.deliveries.models import Delivery
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from app.payments_direct.models import DisputeBlock, PaymentDispute
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass
class DisputeSeed:
    area_id: int
    courier_id: int
    merchant_id: int
    nbhd_id: int
    admin_id: int


@pytest.fixture
def payment_stub():
    from app.payments.safe2pay_stub import PaymentStubAdapter

    return PaymentStubAdapter(scenario="approved")


@pytest_asyncio.fixture
async def dispute_seed(session_factory: async_sessionmaker[AsyncSession]) -> DisputeSeed:
    async with session_factory() as s:
        area = Area(codename="padua", name="Pádua", config={})
        s.add(area)
        await s.flush()
        nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
        s.add(nbhd)
        await s.flush()
        user = User(
            email="c@example.com",
            name="C",
            password_hash=hash_password("correct-horse-staple-10"),
            platform_role="user",
        )
        admin = User(
            email="adm@example.com",
            name="Adm",
            password_hash=hash_password("correct-horse-staple-10"),
            platform_role="admin_plataforma",
        )
        s.add_all([user, admin])
        await s.flush()
        courier = Courier(
            area_id=area.id,
            user_id=user.id,
            cpf="39053344705",
            full_name="C",
            phone_e164="+5522999990000",
            email="c@example.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
            is_online=True,
            max_concurrent=2,
        )
        s.add(courier)
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
        await s.commit()
        return DisputeSeed(
            area_id=area.id,
            courier_id=courier.id,
            merchant_id=merchant.id,
            nbhd_id=nbhd.id,
            admin_id=admin.id,
        )


_token_seq = iter(range(1_000_000))


async def _open_dispute(
    s: AsyncSession, seed: DisputeSeed, *, fee_cents: int = 200, opened_at: datetime
) -> PaymentDispute:
    """Create a direct delivery + an OPEN dispute on it (the courier's 'não recebi')."""
    delivery = Delivery(
        area_id=seed.area_id,
        merchant_id=seed.merchant_id,
        courier_id=seed.courier_id,
        state="ENTREGUE",
        dispatch_mode="direct",
        payment_method="direct",
        proof_method="photo",
        pickup_address="a",
        dropoff_address="b",
        dropoff_neighborhood_id=seed.nbhd_id,
        fee_cents=fee_cents,
        items_quantity=1,
        public_token=f"DTOK{next(_token_seq):022d}",
        origin="manual",
    )
    s.add(delivery)
    await s.flush()
    dispute = PaymentDispute(
        area_id=seed.area_id,
        delivery_id=delivery.id,
        courier_id=seed.courier_id,
        status="open",
        reason="não recebi",
        opened_at=opened_at,
    )
    s.add(dispute)
    await s.flush()
    return dispute


@pytest.mark.asyncio
async def test_procedente_records_adjustment_and_audits(
    dispute_seed, session_factory, payment_stub
) -> None:
    from app.audit.models import AuditLog
    from app.payments_direct import disputes

    now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
    async with session_factory() as s:
        dispute = await _open_dispute(s, dispute_seed, fee_cents=300, opened_at=now)
        await s.commit()
        dispute_id = dispute.id

    async with session_factory() as s:
        decided, block = await disputes.decide_dispute(
            s,
            dispute_id=dispute_id,
            area_id=dispute_seed.area_id,
            decision="procedente",
            actor_id=dispute_seed.admin_id,
            payment=payment_stub,
            now=now,
        )
        await s.commit()
        assert decided.decision == "procedente"
        assert decided.status == "resolved"
        # Direct delivery → credit equal to its recorded platform fee.
        assert decided.adjustment_cents == 300
        assert block is None  # only 1 procedente so far

    async with session_factory() as s:
        audits = (
            await s.execute(select(AuditLog).where(AuditLog.action == "dispute.decided"))
        ).scalars().all()
        assert len(audits) == 1


@pytest.mark.asyncio
async def test_improcedente_moves_no_money(dispute_seed, session_factory, payment_stub) -> None:
    from app.payments_direct import disputes

    now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
    async with session_factory() as s:
        dispute = await _open_dispute(s, dispute_seed, fee_cents=300, opened_at=now)
        await s.commit()
        dispute_id = dispute.id

    async with session_factory() as s:
        decided, block = await disputes.decide_dispute(
            s,
            dispute_id=dispute_id,
            area_id=dispute_seed.area_id,
            decision="improcedente",
            actor_id=dispute_seed.admin_id,
            payment=payment_stub,
            now=now,
        )
        await s.commit()
        assert decided.decision == "improcedente"
        assert decided.adjustment_cents == 0
        assert block is None


@pytest.mark.asyncio
async def test_two_procedentes_in_30d_open_90d_block(
    dispute_seed, session_factory, payment_stub
) -> None:
    from app.payments_direct import disputes

    t0 = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
    t1 = t0 + timedelta(days=20)  # within the 30d window

    async with session_factory() as s:
        d1 = await _open_dispute(s, dispute_seed, opened_at=t0)
        d2 = await _open_dispute(s, dispute_seed, opened_at=t1)
        await s.commit()
        d1_id, d2_id = d1.id, d2.id

    # First procedente — no block yet.
    async with session_factory() as s:
        _, block = await disputes.decide_dispute(
            s,
            dispute_id=d1_id,
            area_id=dispute_seed.area_id,
            decision="procedente",
            actor_id=dispute_seed.admin_id,
            payment=payment_stub,
            now=t0,
        )
        await s.commit()
        assert block is None

    # Second procedente within 30d → 90-day block opens.
    async with session_factory() as s:
        _, block = await disputes.decide_dispute(
            s,
            dispute_id=d2_id,
            area_id=dispute_seed.area_id,
            decision="procedente",
            actor_id=dispute_seed.admin_id,
            payment=payment_stub,
            now=t1,
        )
        await s.commit()
        assert block is not None
        assert block.status == "active"
        # 90 days exactly.
        assert (block.expires_at - block.opened_at).days == 90

    # Blocked now (before 90d).
    async with session_factory() as s:
        assert await disputes.is_blocked(
            s, area_id=dispute_seed.area_id, courier_id=dispute_seed.courier_id, now=t1
        )

    # Expire sweep at 91 days → block expires, no longer blocked.
    expired = await disputes.expire_blocks(session_factory, now=t1 + timedelta(days=91))
    assert expired == 1
    async with session_factory() as s:
        assert not await disputes.is_blocked(
            s,
            area_id=dispute_seed.area_id,
            courier_id=dispute_seed.courier_id,
            now=t1 + timedelta(days=91),
        )


@pytest.mark.asyncio
async def test_procedentes_outside_window_do_not_block(
    dispute_seed, session_factory, payment_stub
) -> None:
    from app.payments_direct import disputes

    t0 = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
    t1 = t0 + timedelta(days=40)  # OUTSIDE the 30d window

    async with session_factory() as s:
        d1 = await _open_dispute(s, dispute_seed, opened_at=t0)
        d2 = await _open_dispute(s, dispute_seed, opened_at=t1)
        await s.commit()
        d1_id, d2_id = d1.id, d2.id

    async with session_factory() as s:
        await disputes.decide_dispute(
            s,
            dispute_id=d1_id,
            area_id=dispute_seed.area_id,
            decision="procedente",
            actor_id=dispute_seed.admin_id,
            payment=payment_stub,
            now=t0,
        )
        await s.commit()

    async with session_factory() as s:
        _, block = await disputes.decide_dispute(
            s,
            dispute_id=d2_id,
            area_id=dispute_seed.area_id,
            decision="procedente",
            actor_id=dispute_seed.admin_id,
            payment=payment_stub,
            now=t1,
        )
        await s.commit()
        # Only 1 procedente within the 30d window ending at t1 → no block.
        assert block is None


@pytest.mark.asyncio
async def test_blocked_courier_cannot_confirm_direct(
    dispute_seed, session_factory
) -> None:
    from app.payments_direct.service import DirectModalityBlockedError, confirm_direct_payment

    now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
    async with session_factory() as s:
        s.add(
            DisputeBlock(
                area_id=dispute_seed.area_id,
                courier_id=dispute_seed.courier_id,
                status="active",
                opened_at=now,
                expires_at=datetime.now(UTC) + timedelta(days=90),
                reason="test",
            )
        )
        delivery = Delivery(
            area_id=dispute_seed.area_id,
            merchant_id=dispute_seed.merchant_id,
            courier_id=dispute_seed.courier_id,
            state="ENTREGUE",
            dispatch_mode="direct",
            payment_method="direct",
            proof_method="photo",
            pickup_address="a",
            dropoff_address="b",
            dropoff_neighborhood_id=dispute_seed.nbhd_id,
            fee_cents=200,
            items_quantity=1,
            public_token=f"BTOK{next(_token_seq):022d}",
            origin="manual",
        )
        s.add(delivery)
        await s.flush()
        await s.commit()
        delivery_id = delivery.id

    async with session_factory() as s:
        delivery = await s.get(Delivery, delivery_id)
        with pytest.raises(DirectModalityBlockedError):
            await confirm_direct_payment(
                s,
                delivery=delivery,
                courier_id=dispute_seed.courier_id,
                outcome="cash",
                amount_cents=2000,
            )
