"""Dispute financial resolution + RN-027 block (Phase 15 — REQ-039 / D-03).

The financial CONSEQUENCE of a "não recebi" dispute (the triage UI is Phase 13; here is
the money). A platform admin decides `procedente` | `improcedente`:

- `procedente`: the courier was right — issue a refund/credit via the `PaymentPort` for
  the disputed amount (`refund`), record `adjustment_cents`. AUDITED (TH-05). It also
  counts toward RN-027.
- `improcedente`: no money moves; recorded + AUDITED.

RN-027: when a courier reaches `dispute_block_threshold` (2) `procedente` decisions
within `dispute_block_window_days` (30) → open a `DisputeBlock` of
`dispute_block_duration_days` (90), blocking the direct modality for that courier
(`is_blocked` guard on direct confirmation). Idempotent: only one ACTIVE block per
courier; a cron (`expire_blocks`) expires them at 90d. All values parametrised (D-07).

Money in integer cents (DRV-009); datetimes aware UTC (TD-010). No PII in any audit
payload (TH-06 — only ids/decisions/amounts).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.audit.service import write_audit
from app.core.config import settings
from app.core.exceptions import AppError, NotFoundError
from app.db.mixins import ensure_aware_utc
from app.payments.port import PaymentPort
from app.payments_direct.models import DisputeBlock, PaymentDispute

logger = structlog.get_logger("payments_direct.disputes")

DISPUTE_DECISIONS = ("procedente", "improcedente")


class DisputeAlreadyDecidedError(AppError):
    """The dispute has already been decided (no re-decision)."""

    status_code = 409
    code = "dispute_already_decided"

    def __init__(self) -> None:
        super().__init__("Esta disputa já foi decidida.")


class InvalidDecisionError(AppError):
    status_code = 422
    code = "invalid_decision"

    def __init__(self) -> None:
        super().__init__("Decisão inválida (use procedente ou improcedente).")


async def _active_block(
    session: AsyncSession, *, area_id: int, courier_id: int, now: datetime
) -> DisputeBlock | None:
    """The courier's active, non-expired dispute block (or None)."""
    stmt = select(DisputeBlock).where(
        DisputeBlock.area_id == area_id,
        DisputeBlock.courier_id == courier_id,
        DisputeBlock.status == "active",
        DisputeBlock.expires_at > now,
    )
    return (await session.execute(stmt)).scalars().first()


async def is_blocked(
    session: AsyncSession, *, area_id: int, courier_id: int, now: datetime | None = None
) -> bool:
    """True if the courier has an active dispute block (direct modality blocked — RN-027)."""
    now = ensure_aware_utc(now or datetime.now(UTC))
    return await _active_block(session, area_id=area_id, courier_id=courier_id, now=now) is not None


async def _count_recent_procedentes(
    session: AsyncSession, *, area_id: int, courier_id: int, since: datetime
) -> int:
    """Count `procedente` decisions for a courier decided since `since` (RN-027 window)."""
    stmt = select(PaymentDispute).where(
        PaymentDispute.area_id == area_id,
        PaymentDispute.courier_id == courier_id,
        PaymentDispute.decision == "procedente",
        PaymentDispute.decided_at >= since,
    )
    return len((await session.execute(stmt)).scalars().all())


async def decide_dispute(
    session: AsyncSession,
    *,
    dispute_id: int,
    area_id: int,
    decision: str,
    actor_id: int,
    payment: PaymentPort,
    now: datetime | None = None,
) -> tuple[PaymentDispute, DisputeBlock | None]:
    """Decide a dispute financially (D-03); procedente refunds + may open a block (RN-027).

    Area-scoped (IDOR → 404). A `procedente` decision refunds the disputed amount via the
    PaymentPort and counts toward RN-027; reaching the threshold within the window opens a
    90-day `DisputeBlock` (idempotent — one active block). AUDITED (TH-05). The caller
    commits. Returns (dispute, block|None).
    """
    if decision not in DISPUTE_DECISIONS:
        raise InvalidDecisionError()
    now = ensure_aware_utc(now or datetime.now(UTC))

    stmt = select(PaymentDispute).where(
        PaymentDispute.id == dispute_id, PaymentDispute.area_id == area_id
    )
    dispute = (await session.execute(stmt)).scalars().first()
    if dispute is None:
        raise NotFoundError("Disputa não encontrada.")
    if dispute.decision is not None:
        raise DisputeAlreadyDecidedError()

    adjustment = 0
    if decision == "procedente":
        # Issue the financial adjustment via the PaymentPort (refund/credit on the
        # delivery charge). The disputed amount is the delivery's recorded fee/estimate.
        adjustment = await _refund_dispute(session, dispute=dispute, payment=payment)

    dispute.decision = decision
    dispute.decided_at = now
    dispute.decided_by = actor_id
    dispute.adjustment_cents = adjustment
    dispute.status = "resolved"
    await session.flush()

    await write_audit(
        session,
        actor_id=actor_id,
        action="dispute.decided",
        area_id=area_id,
        before={"status": "open"},
        after={
            "status": "resolved",
            "decision": decision,
            "adjustment_cents": adjustment,
            "dispute_id": dispute.id,
        },
    )

    block: DisputeBlock | None = None
    if decision == "procedente":
        block = await _maybe_open_block(
            session,
            area_id=area_id,
            courier_id=dispute.courier_id,
            actor_id=actor_id,
            now=now,
        )

    logger.info(
        "dispute.decided",
        area_id=area_id,
        dispute_id=dispute.id,
        decision=decision,
        adjustment_cents=adjustment,
        blocked=block is not None,
    )
    return dispute, block


async def _refund_dispute(
    session: AsyncSession, *, dispute: PaymentDispute, payment: PaymentPort
) -> int:
    """Refund/credit the disputed amount via the PaymentPort. Returns cents adjusted.

    For a direct delivery there is no online charge, so the adjustment is RECORDED as a
    credit equal to the delivery's platform fee (the amount the platform would have
    invoiced). When an online charge exists, it is refunded via the PaymentPort (TH-07 —
    confirmed route, distinct Pix/Card). Never moves money without the charge present.
    """
    from app.deliveries.models import Delivery
    from app.payments import repo as pay_repo

    charge = await pay_repo.get_charge_by_key(
        session, idempotency_key=f"dlv_{dispute.delivery_id}"
    )
    if charge is not None and charge.transaction_id is not None and charge.status == "paid":
        await payment.refund(
            transaction_id=charge.transaction_id,
            amount_cents=charge.amount_cents,
            method=charge.method,
        )
        charge.status = "refunded"
        await session.flush()
        return charge.amount_cents

    # Direct delivery — record a credit equal to its platform fee (waived invoice line).
    delivery = await session.get(Delivery, dispute.delivery_id)
    return delivery.fee_cents if delivery is not None else 0


async def _maybe_open_block(
    session: AsyncSession,
    *,
    area_id: int,
    courier_id: int,
    actor_id: int,
    now: datetime,
) -> DisputeBlock | None:
    """Open a 90-day block if the courier hit the RN-027 threshold (idempotent)."""
    # Already blocked → idempotent no-op.
    if await _active_block(session, area_id=area_id, courier_id=courier_id, now=now):
        return None
    window_start = now - timedelta(days=settings.dispute_block_window_days)
    count = await _count_recent_procedentes(
        session, area_id=area_id, courier_id=courier_id, since=window_start
    )
    if count < settings.dispute_block_threshold:
        return None
    block = DisputeBlock(
        area_id=area_id,
        courier_id=courier_id,
        status="active",
        opened_at=now,
        expires_at=now + timedelta(days=settings.dispute_block_duration_days),
        reason=f"{count} disputas procedentes em {settings.dispute_block_window_days}d (RN-027)",
    )
    session.add(block)
    await session.flush()
    await write_audit(
        session,
        actor_id=actor_id,
        action="dispute_block.opened",
        area_id=area_id,
        after={
            "courier_id": courier_id,
            "expires_at": block.expires_at.isoformat(),
            "procedente_count": count,
        },
    )
    logger.info("dispute_block.opened", area_id=area_id, courier_id=courier_id)
    return block


async def expire_blocks(
    session_factory: async_sessionmaker[AsyncSession], *, now: datetime | None = None
) -> int:
    """Cron: expire active dispute blocks past their 90-day window (RN-027). Idempotent."""
    now = ensure_aware_utc(now or datetime.now(UTC))
    expired = 0
    async with session_factory() as session:
        stmt = select(DisputeBlock).where(DisputeBlock.status == "active")
        for block in (await session.execute(stmt)).scalars().all():
            if ensure_aware_utc(block.expires_at) <= now:
                block.status = "expired"
                expired += 1
        await session.commit()
    logger.info("dispute_block.expire_sweep", expired=expired)
    return expired
