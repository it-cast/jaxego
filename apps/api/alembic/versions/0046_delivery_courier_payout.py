"""delivery courier payout tracking

Revision ID: 0046
Revises: 0045
Create Date: 2026-07-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0046"
down_revision = "0045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deliveries",
        sa.Column("courier_payout_transaction_id", sa.String(64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("deliveries", "courier_payout_transaction_id")
