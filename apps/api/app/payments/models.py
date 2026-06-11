"""Safe2Pay núcleo models (Phase 10 — platform_charges, escrow_ledger, webhook_events).

Money is integer CENTS everywhere (never Float — DRV-009). All datetimes are aware UTC
(UTC_DATETIME / TD-010). The three tables:

- `PlatformCharge` — every online charge (subscription or delivery). `idempotency_key`
  is UNIQUE → a re-charge with the same key is a no-op (TH-D). `transaction_id` is the
  Safe2Pay `IdTransaction`, indexed for webhook/reconcile lookup. `kind` ∈
  {subscription, delivery}; `status` ∈ {open, paid, failed, refunded, canceled}.

- `EscrowLedger` — the internal 24h escrow (RN-006), a domain ledger independent of the
  PSP. A delivery's corrida is HELD on charge; `release_escrow` moves it to RELEASED only
  FINALIZADA+24h with no dispute (TH-G). State ∈ {HELD, RELEASED, REFUNDED, FROZEN}.
  `finalized_at` is indexed for the cron sweep.

- `PaymentWebhookEvent` — webhook idempotency. UNIQUE(transaction_id, status) makes a
  duplicate Safe2Pay re-send a no-op (TH-E / skill A3). `payload` is logged BEFORE
  processing (without card PII).

`PlatformCharge`/`EscrowLedger` are AREA-SCOPED (AreaScopedMixin → IDOR closed in the
WHERE clause). `PaymentWebhookEvent` is GLOBAL (the webhook arrives before we resolve a
tenant; area is nullable, filled when known).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin

CHARGE_KINDS = ("subscription", "delivery")
CHARGE_STATUSES = ("open", "paid", "failed", "refunded", "canceled")
ESCROW_STATES = ("HELD", "RELEASED", "REFUNDED", "FROZEN")


class PlatformCharge(Base, AreaScopedMixin, TimestampMixin):
    """An online charge (subscription or delivery). Idempotent by idempotency_key."""

    __tablename__ = "platform_charges"
    __table_args__ = (
        # TH-D: one charge per idempotency key (re-charge is a no-op).
        UniqueConstraint("idempotency_key", name="uq_platform_charges_idempotency_key"),
        # Webhook / reconcile lookup by Safe2Pay transaction id.
        Index("ix_platform_charges_transaction_id", "transaction_id"),
        # Delinquency / cron sweep of open subscription charges by due date.
        Index("ix_platform_charges_status_due_at", "status", "due_at"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)

    # Business idempotency key (e.g. `dlv_{id}` / `sub_{id}_{period}`) — UNIQUE.
    idempotency_key: Mapped[str] = mapped_column(String(80), nullable=False)
    # Safe2Pay IdTransaction (nullable until the gateway returns it).
    transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str] = mapped_column(String(8), nullable=False)  # card | pix
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")

    # Link back to the originating entity (one of the two is set).
    subscription_id: Mapped[int | None] = mapped_column(BIG_ID, nullable=True, index=True)
    delivery_id: Mapped[int | None] = mapped_column(BIG_ID, nullable=True, index=True)

    # Subscription charges carry the due date (cron + delinquency). aware-UTC.
    due_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)


class EscrowLedger(Base, AreaScopedMixin, TimestampMixin):
    """Internal 24h escrow of a delivery's corrida (RN-006). Released only via cron."""

    __tablename__ = "escrow_ledger"
    __table_args__ = (
        # Cron sweep: holds ready for release by state + finalized_at.
        Index("ix_escrow_ledger_state_finalized_at", "state", "finalized_at"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)

    delivery_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("deliveries.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    courier_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="HELD")
    # When the delivery was FINALIZADA (set on finalisation; the 24h clock starts here).
    finalized_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)


class PaymentWebhookEvent(Base, TimestampMixin):
    """Webhook idempotency ledger. UNIQUE(transaction_id, status) → one effect (TH-E).

    GLOBAL (not area-scoped): the webhook arrives before we resolve a tenant; `area_id`
    is nullable and filled when the linked charge is known. `payload` is logged BEFORE
    processing (skill A3 / D-04) — without card PII.
    """

    __tablename__ = "payment_webhook_events"
    __table_args__ = (
        UniqueConstraint("transaction_id", "status", name="uq_payment_webhook_events_tx_status"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    area_id: Mapped[int | None] = mapped_column(BIG_ID, nullable=True)
    transaction_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
