"""Withdrawal model (Phase 15 — REQ-038 / D-04 / TH-01/TH-02).

A courier withdraws from the RELEASED escrow balance. Money is integer CENTS (DRV-009);
datetimes aware UTC (TD-010). AREA-SCOPED (AreaScopedMixin → IDOR closed in the WHERE
clause; the withdrawal is also scoped to the owning courier_id — TH-01).

- `reference` is the business idempotency key (UNIQUE) — one payout per reference, so a
  retried request is a no-op (TH-02). `status` ∈ {pending, paid, failed}: a payout that
  fails compensates the balance back and ends `failed`; a successful payout ends `paid`.
- `transaction_id` is the Safe2Pay payout IdTransaction (set on success).

The withdrawable balance itself is not a stored column: it is DERIVED from the RELEASED
escrow ledger minus prior non-failed withdrawals (computed under `SELECT ... FOR UPDATE`
on the ledger rows — TH-02 anti double-spend).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin

WITHDRAWAL_STATUSES = ("pending", "paid", "failed")


class Withdrawal(Base, AreaScopedMixin, TimestampMixin):
    """A courier's withdrawal of released escrow balance (idempotent by reference)."""

    __tablename__ = "withdrawals"
    __table_args__ = (
        # TH-02: one payout per reference (a retried request is a no-op).
        UniqueConstraint("reference", name="uq_withdrawals_reference"),
        Index("ix_withdrawals_courier_id", "courier_id"),
        Index("ix_withdrawals_status", "status"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    courier_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    # Business idempotency key (e.g. `wd_{courier}_{ts}`) — UNIQUE (TH-02).
    reference: Mapped[str] = mapped_column(String(80), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    # pending | paid | failed.
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    # Safe2Pay payout IdTransaction (set on success).
    transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
