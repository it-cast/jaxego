"""Direct payment confirmation (RN-026 / D-05 — F-06).

The courier confirms "Recebi R$ X" (cash/pix) → `DirectPaymentConfirmation`. "Não
recebi" (`not_received`) still records the confirmation AND opens a `PaymentDispute`
(status `open` — mediação is Phase 11). Authorisation: only the courier assigned to
the delivery may confirm (ownership in the query — TH-7). aware-UTC (TD-010).

This runs AFTER the delivery is ENTREGUE (the proof transition already happened); the
confirmation is about the money, not the state. The state is therefore left as-is;
"não recebi" does NOT block ENTREGUE — it only opens the dispute record.
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.deliveries.models import Delivery
from app.payments_direct.models import DirectPaymentConfirmation, PaymentDispute

logger = structlog.get_logger("payments_direct.service")


async def confirm_direct_payment(
    session: AsyncSession,
    *,
    delivery: Delivery,
    courier_id: int,
    outcome: str,
    amount_cents: int | None,
) -> tuple[DirectPaymentConfirmation, PaymentDispute | None]:
    """Record the courier's direct-payment confirmation (RN-026).

    `outcome` ∈ {cash, pix, not_received}. `not_received` also opens a dispute.
    Returns (confirmation, dispute|None). The caller commits.
    """
    now = datetime.now(UTC)  # AWARE — TD-010
    confirmation = DirectPaymentConfirmation(
        area_id=delivery.area_id,
        delivery_id=delivery.id,
        courier_id=courier_id,
        outcome=outcome,
        amount_cents=amount_cents if outcome in ("cash", "pix") else None,
    )
    session.add(confirmation)

    dispute: PaymentDispute | None = None
    if outcome == "not_received":
        dispute = PaymentDispute(
            area_id=delivery.area_id,
            delivery_id=delivery.id,
            courier_id=courier_id,
            status="open",
            reason="courier reported payment not received",
            opened_at=now,
        )
        session.add(dispute)

    await session.flush()
    # No PII — only ids + outcome (A09).
    logger.info(
        "direct_payment.confirmed",
        area_id=delivery.area_id,
        delivery_id=delivery.id,
        outcome=outcome,
        dispute_opened=dispute is not None,
    )
    return confirmation, dispute


async def has_open_dispute(session: AsyncSession, *, delivery_id: int) -> bool:
    """True if the delivery has an OPEN payment dispute (blocks 24h finalisation)."""
    from sqlalchemy import select

    stmt = select(PaymentDispute.id).where(
        PaymentDispute.delivery_id == delivery_id,
        PaymentDispute.status == "open",
    )
    return (await session.execute(stmt)).first() is not None
