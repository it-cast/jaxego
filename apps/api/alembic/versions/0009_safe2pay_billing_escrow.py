"""safe2pay billing + escrow + webhooks (Phase 10 — F-03/F-07)

Adds the Safe2Pay núcleo: `platform_charges` (idempotent online charges),
`escrow_ledger` (internal 24h escrow, RN-006), `payment_webhook_events` (webhook
idempotency UNIQUE(transaction_id,status)), the recurring-billing columns on
`merchant_subscriptions` (billing_status, payment_method, cycle, amount_cents, due_at,
safe2pay_token AES-256-GCM, scheduled_plan_id, PIX-automatic state), and
`couriers.s2p_recipient_id` (subaccount on MEI approval).

REVERSIBLE (lição da 0006/0008): `downgrade` drops tables children-first and does NOT
call `op.drop_index` on indexes that back a dropped table (drop_table removes them;
dropping a FK-backing index first trips MySQL errno 1553). The revision id is short
(28 chars ≤ 32 — lição da 0009 alembic_version VARCHAR(32)).

Revision ID: 0009_safe2pay_billing_escrow
Revises: 0008_proofs_tracking_notif
Create Date: 2026-06-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0009_safe2pay_billing_escrow"
down_revision: str | None = "0008_proofs_tracking_notif"
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
    # --- merchant_subscriptions: recurring-billing columns (Phase 10) ---
    op.add_column(
        "merchant_subscriptions",
        sa.Column("billing_status", sa.String(length=16), nullable=False, server_default="trial"),
    )
    op.add_column(
        "merchant_subscriptions", sa.Column("payment_method", sa.String(length=8), nullable=True)
    )
    op.add_column("merchant_subscriptions", sa.Column("cycle", sa.String(length=10), nullable=True))
    op.add_column(
        "merchant_subscriptions",
        sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("merchant_subscriptions", sa.Column("due_at", _dt(), nullable=True))
    op.add_column(
        "merchant_subscriptions", sa.Column("safe2pay_token", sa.String(length=512), nullable=True)
    )
    op.add_column(
        "merchant_subscriptions", sa.Column("scheduled_plan_id", sa.BigInteger(), nullable=True)
    )
    op.add_column(
        "merchant_subscriptions",
        sa.Column("pix_autorizacao_id", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "merchant_subscriptions",
        sa.Column("pix_autorizacao_status", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "merchant_subscriptions", sa.Column("pix_qr_code", sa.String(length=2048), nullable=True)
    )
    op.add_column(
        "merchant_subscriptions", sa.Column("pix_qr_code_base64", sa.Text(), nullable=True)
    )

    # --- couriers.s2p_recipient_id (subaccount on MEI approval — RN-010) ---
    op.add_column("couriers", sa.Column("s2p_recipient_id", sa.String(length=100), nullable=True))

    # --- platform_charges ---
    op.create_table(
        "platform_charges",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=80), nullable=False),
        sa.Column("transaction_id", sa.String(length=100), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(length=8), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("subscription_id", sa.BigInteger(), nullable=True),
        sa.Column("delivery_id", sa.BigInteger(), nullable=True),
        sa.Column("due_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_platform_charges")),
        _area_fk("platform_charges"),
        sa.UniqueConstraint("idempotency_key", name="uq_platform_charges_idempotency_key"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_platform_charges_area_id"), "platform_charges", ["area_id"])
    op.create_index("ix_platform_charges_transaction_id", "platform_charges", ["transaction_id"])
    op.create_index("ix_platform_charges_status_due_at", "platform_charges", ["status", "due_at"])
    op.create_index("ix_platform_charges_subscription_id", "platform_charges", ["subscription_id"])
    op.create_index("ix_platform_charges_delivery_id", "platform_charges", ["delivery_id"])

    # --- escrow_ledger ---
    op.create_table(
        "escrow_ledger",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("delivery_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("finalized_at", _dt(), nullable=True),
        sa.Column("released_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_escrow_ledger")),
        _area_fk("escrow_ledger"),
        sa.ForeignKeyConstraint(
            ["delivery_id"],
            ["deliveries.id"],
            name=op.f("fk_escrow_ledger_delivery_id_deliveries"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["courier_id"],
            ["couriers.id"],
            name=op.f("fk_escrow_ledger_courier_id_couriers"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_escrow_ledger_area_id"), "escrow_ledger", ["area_id"])
    op.create_index("ix_escrow_ledger_delivery_id", "escrow_ledger", ["delivery_id"])
    op.create_index("ix_escrow_ledger_courier_id", "escrow_ledger", ["courier_id"])
    op.create_index(
        "ix_escrow_ledger_state_finalized_at", "escrow_ledger", ["state", "finalized_at"]
    )

    # --- payment_webhook_events (GLOBAL — area nullable; UNIQUE idempotency) ---
    op.create_table(
        "payment_webhook_events",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=True),
        sa.Column("transaction_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_webhook_events")),
        sa.UniqueConstraint("transaction_id", "status", name="uq_payment_webhook_events_tx_status"),
        **_TABLE_KW,
    )


def downgrade() -> None:
    # Drop tables children-first. NO explicit drop_index — drop_table removes the
    # table's indexes with it; dropping a FK-backing index first trips MySQL errno 1553
    # (lição da 0006/0008).
    op.drop_table("payment_webhook_events")
    op.drop_table("escrow_ledger")
    op.drop_table("platform_charges")

    op.drop_column("couriers", "s2p_recipient_id")

    op.drop_column("merchant_subscriptions", "pix_qr_code_base64")
    op.drop_column("merchant_subscriptions", "pix_qr_code")
    op.drop_column("merchant_subscriptions", "pix_autorizacao_status")
    op.drop_column("merchant_subscriptions", "pix_autorizacao_id")
    op.drop_column("merchant_subscriptions", "scheduled_plan_id")
    op.drop_column("merchant_subscriptions", "safe2pay_token")
    op.drop_column("merchant_subscriptions", "due_at")
    op.drop_column("merchant_subscriptions", "amount_cents")
    op.drop_column("merchant_subscriptions", "cycle")
    op.drop_column("merchant_subscriptions", "payment_method")
    op.drop_column("merchant_subscriptions", "billing_status")
