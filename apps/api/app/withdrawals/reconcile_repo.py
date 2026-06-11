"""Reconciliation queries for withdrawals (Phase 15 — D-05).

Paid courier repasses (withdrawals) appear on the Safe2Pay extrato; the daily
reconciliation cross-checks them too. Single query, index-backed by status — no N+1.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.withdrawals.models import Withdrawal


async def paid_withdrawals_between(
    session: AsyncSession, *, since: datetime, until: datetime
) -> list[Withdrawal]:
    """Paid withdrawals with a transaction id settled in [since, until] (single query)."""
    stmt = select(Withdrawal).where(
        Withdrawal.status == "paid",
        Withdrawal.transaction_id.is_not(None),
        Withdrawal.settled_at >= since,
        Withdrawal.settled_at <= until,
    )
    return list((await session.execute(stmt)).scalars().all())
