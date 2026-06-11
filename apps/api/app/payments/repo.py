"""Payment persistence — idempotent charge writes, webhook dedup, escrow queries.

Every charge write is idempotent by `idempotency_key` (TH-D): `record_charge` is a no-op
if a row with that key already exists (the UNIQUE constraint is the source of truth; we
check-then-insert under the caller's transaction, and the constraint backstops a race).
`mark_webhook_seen` inserts into `payment_webhook_events` and returns False when the
(transaction_id, status) pair already exists (TH-E). Queries use the declared indexes —
no N+1, no table scan (Gate 8).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.payments.models import EscrowLedger, PaymentWebhookEvent, PlatformCharge


async def get_charge_by_key(
    session: AsyncSession, *, idempotency_key: str
) -> PlatformCharge | None:
    """Load a charge by its business idempotency key (or None)."""
    stmt = select(PlatformCharge).where(PlatformCharge.idempotency_key == idempotency_key)
    return (await session.execute(stmt)).scalars().first()


async def get_charge_for_area(
    session: AsyncSession, *, idempotency_key: str, area_id: int
) -> PlatformCharge | None:
    """Load a charge scoped to an area (TH-H — IDOR closed in the WHERE clause)."""
    stmt = select(PlatformCharge).where(
        PlatformCharge.idempotency_key == idempotency_key,
        PlatformCharge.area_id == area_id,
    )
    return (await session.execute(stmt)).scalars().first()


async def record_charge(
    session: AsyncSession,
    *,
    area_id: int,
    idempotency_key: str,
    transaction_id: str | None,
    amount_cents: int,
    method: str,
    kind: str,
    status: str,
    subscription_id: int | None = None,
    delivery_id: int | None = None,
    due_at: datetime | None = None,
) -> PlatformCharge:
    """Insert a charge idempotently — a duplicate idempotency_key is a no-op (TH-D)."""
    existing = await get_charge_by_key(session, idempotency_key=idempotency_key)
    if existing is not None:
        return existing
    charge = PlatformCharge(
        area_id=area_id,
        idempotency_key=idempotency_key,
        transaction_id=transaction_id,
        amount_cents=amount_cents,
        method=method,
        kind=kind,
        status=status,
        subscription_id=subscription_id,
        delivery_id=delivery_id,
        due_at=due_at,
    )
    session.add(charge)
    try:
        await session.flush()
    except IntegrityError:
        # Lost a race on the UNIQUE — the other writer won; return its row.
        await session.rollback()
        existing = await get_charge_by_key(session, idempotency_key=idempotency_key)
        if existing is None:  # pragma: no cover — defensive
            raise
        return existing
    return charge


async def mark_webhook_seen(
    session: AsyncSession,
    *,
    area_id: int | None,
    transaction_id: str,
    status: str,
    payload: str | None = None,
) -> bool:
    """Insert a webhook event; return False if (tx,status) was already seen (TH-E)."""
    stmt = select(PaymentWebhookEvent.id).where(
        PaymentWebhookEvent.transaction_id == transaction_id,
        PaymentWebhookEvent.status == status,
    )
    if (await session.execute(stmt)).first() is not None:
        return False
    event = PaymentWebhookEvent(
        area_id=area_id, transaction_id=transaction_id, status=status, payload=payload
    )
    session.add(event)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        return False
    return True


async def get_charge_by_transaction(
    session: AsyncSession, *, transaction_id: str
) -> PlatformCharge | None:
    """Load a charge by its Safe2Pay transaction id (webhook processing)."""
    stmt = select(PlatformCharge).where(PlatformCharge.transaction_id == transaction_id)
    return (await session.execute(stmt)).scalars().first()


async def list_charges_between(
    session: AsyncSession, *, since: datetime, until: datetime
) -> list[PlatformCharge]:
    """Paid charges with a transaction id in the window (reconciliation — single query)."""
    stmt = select(PlatformCharge).where(
        PlatformCharge.created_at >= since,
        PlatformCharge.created_at <= until,
        PlatformCharge.transaction_id.is_not(None),
        PlatformCharge.status == "paid",
    )
    return list((await session.execute(stmt)).scalars().all())


async def holds_ready_for_release(
    session: AsyncSession, *, finalized_before: datetime
) -> list[EscrowLedger]:
    """HELD escrow rows finalised before the cutoff (cron sweep — index-backed)."""
    stmt = select(EscrowLedger).where(
        EscrowLedger.state == "HELD",
        EscrowLedger.finalized_at.is_not(None),
        EscrowLedger.finalized_at <= finalized_before,
    )
    return list((await session.execute(stmt)).scalars().all())
