"""DirectPaymentConfirmation + PaymentDispute (RN-026 — pagamento direto, F-06 D-05).

When the delivery is paid directly (cash/PIX in person), the courier confirms "Recebi
R$ X" (`DirectPaymentConfirmation`, outcome `cash`/`pix`). "Não recebi" still concludes
the delivery (ENTREGUE) but opens a `PaymentDispute` record (mediação is Phase 11 — here
it is only RECORDED). Both area-scoped, aware-UTC (TD-010). Amounts in integer cents.
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
    # open | resolved (resolution is Phase 11). Born `open`.
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
