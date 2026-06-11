"""DirectPaymentConfirmation + PaymentDispute + DisputeBlock (RN-026/RN-027).

When the delivery is paid directly (cash/PIX in person), the courier confirms "Recebi
R$ X" (`DirectPaymentConfirmation`, outcome `cash`/`pix`). "Não recebi" still concludes
the delivery (ENTREGUE) but opens a `PaymentDispute` record. Phase 15 adds the FINANCIAL
RESOLUTION of that dispute (D-03): a decision (procedente/improcedente); a `procedente`
decision may issue a refund/credit via the `PaymentPort`. RN-027: 2 `procedente`
decisions within 30 days for the same courier → a `DisputeBlock` of 90 days blocks the
direct modality for that courier (audited; a cron expires it).

All area-scoped, aware-UTC (TD-010). Amounts in integer cents.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin

DIRECT_PAYMENT_OUTCOMES = ("cash", "pix", "not_received")


class DirectPaymentConfirmation(Base, AreaScopedMixin, TimestampMixin):
    """The courier's direct-payment confirmation for a delivery (RN-026)."""

    __tablename__ = "direct_payment_confirmations"
    __table_args__ = (
        Index("ix_direct_payment_confirmations_delivery_id", "delivery_id"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("deliveries.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    courier_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    # cash | pix | not_received
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)


class PaymentDispute(Base, AreaScopedMixin, TimestampMixin):
    """A recorded "não recebi" dispute (mediação = Phase 11; here only RECORDED)."""

    __tablename__ = "payment_disputes"
    __table_args__ = (
        Index("ix_payment_disputes_delivery_id", "delivery_id"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("deliveries.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    courier_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    # open | resolved. Born `open`; the Phase 15 decision sets it `resolved`.
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)

    # --- Phase 15 financial decision (D-03 / RN-027) ---
    # NULL while open; procedente | improcedente once decided.
    decision: Mapped[str | None] = mapped_column(String(16), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    decided_by: Mapped[int | None] = mapped_column(BIG_ID, nullable=True)
    # Refund/credit issued for a `procedente` decision, in cents (0 if none).
    adjustment_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)


DISPUTE_DECISIONS = ("procedente", "improcedente")


class DisputeBlock(Base, AreaScopedMixin, TimestampMixin):
    """A 90-day block of the direct modality for a courier (RN-027 / TH-05).

    Opened when a courier reaches 2 `procedente` disputes within 30 days. While active
    (`expires_at` in the future), the direct modality is blocked for that courier (the
    guard on direct confirmation). A cron expires it (`status` open → expired) at 90d.
    The block is AUDITED in the append-only audit_log (TH-05). Idempotent: only one
    active block per courier at a time.
    """

    __tablename__ = "dispute_blocks"
    __table_args__ = (
        Index("ix_dispute_blocks_courier_id", "courier_id"),
        Index("ix_dispute_blocks_status_expires_at", "status", "expires_at"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    courier_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    # active | expired.
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    opened_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
