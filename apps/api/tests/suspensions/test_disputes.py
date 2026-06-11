"""Dispute administrative decision — audited, NO financial effect (T-06 / REQ-044 / DEC-004)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.audit.models import AuditLog
from app.deliveries.models import Delivery
from app.neighborhoods.models import Neighborhood
from app.payments_direct.models import PaymentDispute
from app.suspensions.service import (
    DisputeNotFoundError,
    list_disputes,
    record_dispute_decision,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.suspensions.conftest import SuspensionWorld


async def _make_dispute(
    db_session: AsyncSession, world: SuspensionWorld
) -> PaymentDispute:
    nbhd = Neighborhood(area_id=world.area_id, name="Centro", is_informal=False)
    db_session.add(nbhd)
    await db_session.flush()
    # Minimal delivery to attach the dispute to (merchant_id can be any FK-valid id;
    # here we reuse the courier's area and a fresh merchant-less delivery is not valid,
    # so attach to an arbitrary merchant via the courier's area — use courier_id only).
    from app.merchants.models import Merchant

    merchant = Merchant(
        area_id=world.area_id,
        account_type="cnpj",
        document="11222333000181",
        trade_name="Loja",
        category="restaurante",
        phone_e164="+5522999991111",
        email="loja@example.com",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()
    delivery = Delivery(
        area_id=world.area_id,
        merchant_id=merchant.id,
        courier_id=world.courier_id,
        state="ENTREGUE",
        pickup_address="Rua A, 1",
        dropoff_address="Rua B, 2",
        dropoff_neighborhood_id=nbhd.id,
        public_token="tok_disp_01",
    )
    db_session.add(delivery)
    await db_session.flush()
    dispute = PaymentDispute(
        area_id=world.area_id,
        delivery_id=delivery.id,
        courier_id=world.courier_id,
        status="open",
        reason="não recebi",
        opened_at=datetime.now(UTC),
    )
    db_session.add(dispute)
    await db_session.flush()
    return dispute


@pytest.mark.asyncio
async def test_record_dispute_decision_audited_no_money(
    db_session: AsyncSession, suspension_world: SuspensionWorld
) -> None:
    dispute = await _make_dispute(db_session, suspension_world)
    updated = await record_dispute_decision(
        db_session,
        dispute_id=dispute.id,
        area_id=suspension_world.area_id,
        outcome="procedente",
        actor_id=suspension_world.admin_id,
        note="evidências confirmam",
    )
    assert updated.status == "resolved"  # administrative state only
    actions = [r[0] for r in (await db_session.execute(select(AuditLog.action))).all()]
    assert "dispute.decision_recorded" in actions


@pytest.mark.asyncio
async def test_dispute_decision_scoped_to_area(
    db_session: AsyncSession, suspension_world: SuspensionWorld
) -> None:
    dispute = await _make_dispute(db_session, suspension_world)
    with pytest.raises(DisputeNotFoundError):
        await record_dispute_decision(
            db_session,
            dispute_id=dispute.id,
            area_id=suspension_world.area_id + 999,  # other area → 404
            outcome="improcedente",
            actor_id=suspension_world.admin_id,
        )


@pytest.mark.asyncio
async def test_list_disputes_in_scope(
    db_session: AsyncSession, suspension_world: SuspensionWorld
) -> None:
    await _make_dispute(db_session, suspension_world)
    rows = await list_disputes(db_session, area_id=suspension_world.area_id)
    assert len(rows) == 1
