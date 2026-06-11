"""financeiro back-office: invoices + withdrawals + dispute blocks (Phase 15)

Adds the back-office financial tables (REQ-037/038/039/040):
- `platform_invoices` — monthly platform-fee invoice (1/loja/competência — D-01).
- `invoice_line_items` — the source delivery fees that fed an invoice (derived — TH-03).
- `withdrawals` — courier payout of released escrow balance (idempotent by reference).
- `dispute_blocks` — 90-day direct-modality block (RN-027 / TH-05).
And the financial-decision columns on `payment_disputes` (decision / decided_at /
decided_by / adjustment_cents — D-03).

REVERSIBLE (lição da 0009/0011/0012): `downgrade` drops tables children-first
(`invoice_line_items` before `platform_invoices`) and does NOT call `op.drop_index` on
indexes that back a dropped table (drop_table removes them; dropping a FK-backing index
first trips MySQL errno 1553). The added columns are dropped last. The revision id is
short (≤ 32 — alembic_version VARCHAR(32)).

Revision ID: 0013_financeiro_back_office
Revises: 0012_ai_usage_log
Create Date: 2026-06-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0013_financeiro_back_office"
down_revision: str | None = "0012_ai_usage_log"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE_KW = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}


def _dt() -> sa.types.TypeEngine:
    """DATETIME(6) on MySQL, plain DateTime elsewhere (SQLite dev)."""
    return sa.DateTime(timezone=True).with_variant(mysql.DATETIME(fsp=6), "mysql")


def _area_fk(table: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        ["area_id"],
        ["areas.id"],
        name=op.f(f"fk_{table}_area_id_areas"),
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )


def upgrade() -> None:
    # --- platform_invoices ---
    op.create_table(
        "platform_invoices",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("merchant_id", sa.BigInteger(), nullable=False),
        sa.Column("competence", sa.String(length=7), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("due_at", _dt(), nullable=False),
        sa.Column("closed_at", _dt(), nullable=False),
        sa.Column("paid_at", _dt(), nullable=True),
        sa.Column("transaction_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_platform_invoices")),
        _area_fk("platform_invoices"),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            name=op.f("fk_platform_invoices_merchant_id_merchants"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.UniqueConstraint(
            "area_id", "merchant_id", "competence", name="uq_platform_invoices_area_merch_comp"
        ),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_platform_invoices_area_id"), "platform_invoices", ["area_id"])
    op.create_index(
        "ix_platform_invoices_merchant_id", "platform_invoices", ["merchant_id"]
    )
    op.create_index(
        "ix_platform_invoices_status_due_at", "platform_invoices", ["status", "due_at"]
    )

    # --- invoice_line_items ---
    op.create_table(
        "invoice_line_items",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("invoice_id", sa.BigInteger(), nullable=False),
        sa.Column("delivery_id", sa.BigInteger(), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_invoice_line_items")),
        _area_fk("invoice_line_items"),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["platform_invoices.id"],
            name=op.f("fk_invoice_line_items_invoice_id_platform_invoices"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.UniqueConstraint(
            "invoice_id", "delivery_id", name="uq_invoice_line_items_inv_delivery"
        ),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_invoice_line_items_area_id"), "invoice_line_items", ["area_id"])
    op.create_index("ix_invoice_line_items_invoice_id", "invoice_line_items", ["invoice_id"])

    # --- withdrawals ---
    op.create_table(
        "withdrawals",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        sa.Column("reference", sa.String(length=80), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("transaction_id", sa.String(length=100), nullable=True),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("settled_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_withdrawals")),
        _area_fk("withdrawals"),
        sa.ForeignKeyConstraint(
            ["courier_id"],
            ["couriers.id"],
            name=op.f("fk_withdrawals_courier_id_couriers"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.UniqueConstraint("reference", name="uq_withdrawals_reference"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_withdrawals_area_id"), "withdrawals", ["area_id"])
    op.create_index("ix_withdrawals_courier_id", "withdrawals", ["courier_id"])
    op.create_index("ix_withdrawals_status", "withdrawals", ["status"])

    # --- dispute_blocks ---
    op.create_table(
        "dispute_blocks",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("opened_at", _dt(), nullable=False),
        sa.Column("expires_at", _dt(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dispute_blocks")),
        _area_fk("dispute_blocks"),
        sa.ForeignKeyConstraint(
            ["courier_id"],
            ["couriers.id"],
            name=op.f("fk_dispute_blocks_courier_id_couriers"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_dispute_blocks_area_id"), "dispute_blocks", ["area_id"])
    op.create_index("ix_dispute_blocks_courier_id", "dispute_blocks", ["courier_id"])
    op.create_index(
        "ix_dispute_blocks_status_expires_at", "dispute_blocks", ["status", "expires_at"]
    )

    # --- payment_disputes: financial-decision columns (Phase 15 — D-03) ---
    op.add_column(
        "payment_disputes", sa.Column("decision", sa.String(length=16), nullable=True)
    )
    op.add_column("payment_disputes", sa.Column("decided_at", _dt(), nullable=True))
    op.add_column("payment_disputes", sa.Column("decided_by", sa.BigInteger(), nullable=True))
    op.add_column(
        "payment_disputes", sa.Column("adjustment_cents", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    # Drop the added columns first (reverse order).
    op.drop_column("payment_disputes", "adjustment_cents")
    op.drop_column("payment_disputes", "decided_by")
    op.drop_column("payment_disputes", "decided_at")
    op.drop_column("payment_disputes", "decision")

    # Drop tables children-first. NO explicit drop_index — drop_table removes the table's
    # indexes with it; dropping a FK-backing index first trips MySQL errno 1553 (lição da
    # 0009/0011/0012). invoice_line_items references platform_invoices → drop it first.
    op.drop_table("dispute_blocks")
    op.drop_table("withdrawals")
    op.drop_table("invoice_line_items")
    op.drop_table("platform_invoices")
