"""plan: rename price_cents -> price_monthly_cents, add price_annual_cents

Revision ID: 0038
Revises: 0037
Create Date: 2026-07-07
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "subscription_plans",
        "price_cents",
        new_column_name="price_monthly_cents",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.add_column(
        "subscription_plans",
        sa.Column("price_annual_cents", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute(
        "UPDATE subscription_plans SET price_annual_cents = price_monthly_cents * 10"
    )


def downgrade() -> None:
    op.drop_column("subscription_plans", "price_annual_cents")
    op.alter_column(
        "subscription_plans",
        "price_monthly_cents",
        new_column_name="price_cents",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
