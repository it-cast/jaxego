"""Platform invoice models (Phase 15 — REQ-037, RN-025 / D-01/D-02).

The monthly platform-fee invoice of the back-office direct modality. Money is integer
CENTS everywhere (DRV-009); datetimes are aware UTC (TD-010). Both tables are
AREA-SCOPED (AreaScopedMixin → IDOR closed in the WHERE clause).

- `PlatformInvoice` — one invoice per (merchant, competence) — UNIQUE(area_id,
  merchant_id, competence) makes the closing job idempotent (1/loja/competência —
  D-01 / TH-03). `competence` is the YYYY-MM string of the billed month. `status` ∈
  {open, overdue, paid}. `amount_cents` is the SUM of its line items (derived, never
  user input — TH-03). `due_at` is the parametrised due date (seed — D-07). The fee
  total is aggregated from the platform `delivery` charges of the month (the delivery
  already RECORDED the effective charge — Phase 10).

- `InvoiceLineItem` — one line per source delivery charge that fed the invoice. FK
  RESTRICT back to the invoice (children-first downgrade). `delivery_id` links the
  source delivery; `amount_cents` is that delivery's platform fee.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin

INVOICE_STATUSES = ("open", "overdue", "paid")


class PlatformInvoice(Base, AreaScopedMixin, TimestampMixin):
    """A merchant's monthly platform-fee invoice (1/loja/competência — D-01)."""

    __tablename__ = "platform_invoices"
    __table_args__ = (
        # D-01 / TH-03: exactly one invoice per merchant per competence (idempotent job).
        UniqueConstraint(
            "area_id", "merchant_id", "competence", name="uq_platform_invoices_area_merch_comp"
        ),
        # Overdue sweep / delinquency lookups by status + due date.
        Index("ix_platform_invoices_status_due_at", "status", "due_at"),
        Index("ix_platform_invoices_merchant_id", "merchant_id"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("merchants.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    # The billed month as YYYY-MM (e.g. "2026-05"). aware-UTC closing job sets it.
    competence: Mapped[str] = mapped_column(String(7), nullable=False)
    # SUM of line items (derived — never user input, TH-03).
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # open | overdue | paid.
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    due_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    closed_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    # Safe2Pay IdTransaction of the payment (set when paid via PaymentPort).
    transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True)


class InvoiceLineItem(Base, AreaScopedMixin, TimestampMixin):
    """One source delivery's platform fee that fed an invoice (derived — TH-03)."""

    __tablename__ = "invoice_line_items"
    __table_args__ = (
        Index("ix_invoice_line_items_invoice_id", "invoice_id"),
        # One line per delivery charge per invoice — no double-counting on a re-run.
        UniqueConstraint("invoice_id", "delivery_id", name="uq_invoice_line_items_inv_delivery"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("platform_invoices.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    delivery_id: Mapped[int | None] = mapped_column(BIG_ID, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
