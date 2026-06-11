"""Withdrawal persistence — balance under FOR UPDATE, idempotent writes (TH-01/TH-02).

The withdrawable balance is DERIVED: the SUM of the courier's RELEASED escrow ledger
minus the SUM of its non-failed (pending/paid) withdrawals. `released_holds_for_update`
locks the RELEASED escrow rows `SELECT ... FOR UPDATE` so two concurrent withdrawals
serialize (anti double-spend — TH-02, padrão do aceite da Phase 8). Every query is
scoped to (area_id, courier_id) — IDOR closed in the WHERE clause (TH-01).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.payments.models import EscrowLedger
from app.withdrawals.models import Withdrawal


async def released_holds_for_update(
    session: AsyncSession, *, area_id: int, courier_id: int
) -> list[EscrowLedger]:
    """Lock the courier's RELEASED escrow rows FOR UPDATE (TH-02 — serialise withdrawals)."""
    stmt = (
        select(EscrowLedger)
        .where(
            EscrowLedger.area_id == area_id,
            EscrowLedger.courier_id == courier_id,
            EscrowLedger.state == "RELEASED",
        )
        .with_for_update()
    )
    return list((await session.execute(stmt)).scalars().all())


async def non_failed_withdrawals(
    session: AsyncSession, *, area_id: int, courier_id: int
) -> list[Withdrawal]:
    """All pending/paid withdrawals of the courier (failed ones freed the balance)."""
    stmt = select(Withdrawal).where(
        Withdrawal.area_id == area_id,
        Withdrawal.courier_id == courier_id,
        Withdrawal.status != "failed",
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_by_reference(
    session: AsyncSession, *, reference: str
) -> Withdrawal | None:
    """Load a withdrawal by its idempotency reference (UNIQUE — TH-02)."""
    stmt = select(Withdrawal).where(Withdrawal.reference == reference)
    return (await session.execute(stmt)).scalars().first()


async def released_holds(
    session: AsyncSession, *, area_id: int, courier_id: int, limit: int, offset: int
) -> list[EscrowLedger]:
    """The courier's RELEASED escrow rows (extract credits) — read-only, scoped (TH-01).

    No `FOR UPDATE`: this is the display extract (tela 16), not a balance mutation.
    Index-backed by (area_id, courier_id); newest first; paginated.
    """
    stmt = (
        select(EscrowLedger)
        .where(
            EscrowLedger.area_id == area_id,
            EscrowLedger.courier_id == courier_id,
            EscrowLedger.state == "RELEASED",
        )
        .order_by(EscrowLedger.released_at.desc(), EscrowLedger.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list((await session.execute(stmt)).scalars().all())


async def withdrawals_for_courier(
    session: AsyncSession, *, area_id: int, courier_id: int, limit: int, offset: int
) -> list[Withdrawal]:
    """The courier's withdrawal history (extract debits), scoped (TH-01). Newest first."""
    stmt = (
        select(Withdrawal)
        .where(
            Withdrawal.area_id == area_id,
            Withdrawal.courier_id == courier_id,
        )
        .order_by(Withdrawal.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list((await session.execute(stmt)).scalars().all())


async def available_balance_cents(
    session: AsyncSession, *, area_id: int, courier_id: int
) -> int:
    """Released escrow minus non-failed withdrawals, in integer cents (locks the holds)."""
    holds = await released_holds_for_update(session, area_id=area_id, courier_id=courier_id)
    withdrawn = await non_failed_withdrawals(session, area_id=area_id, courier_id=courier_id)
    return sum(h.amount_cents for h in holds) - sum(w.amount_cents for w in withdrawn)
