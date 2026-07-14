"""merchant credit ledger (saldo da loja) + campos de reconciliação em deliveries

Revision ID: 0047
Revises: 0046
Create Date: 2026-07-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0047"
down_revision = "0046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "merchant_credit_ledger",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "area_id",
            sa.BigInteger(),
            sa.ForeignKey("areas.id", ondelete="RESTRICT", onupdate="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "merchant_id",
            sa.BigInteger(),
            sa.ForeignKey("merchants.id", ondelete="RESTRICT", onupdate="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "delivery_id",
            sa.BigInteger(),
            sa.ForeignKey("deliveries.id", ondelete="RESTRICT", onupdate="RESTRICT"),
            nullable=True,
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index(
        "ix_merchant_credit_ledger_area_id", "merchant_credit_ledger", ["area_id"]
    )
    op.create_index(
        "ix_merchant_credit_ledger_merchant_id", "merchant_credit_ledger", ["merchant_id"]
    )
    op.create_index(
        "ix_merchant_credit_ledger_delivery_id", "merchant_credit_ledger", ["delivery_id"]
    )

    op.add_column(
        "deliveries", sa.Column("pix_courier_price_cents", sa.Integer(), nullable=True)
    )
    op.add_column(
        "deliveries",
        sa.Column(
            "credit_applied_cents", sa.Integer(), nullable=False, server_default="0"
        ),
    )


def downgrade() -> None:
    op.drop_column("deliveries", "credit_applied_cents")
    op.drop_column("deliveries", "pix_courier_price_cents")
    op.drop_table("merchant_credit_ledger")
