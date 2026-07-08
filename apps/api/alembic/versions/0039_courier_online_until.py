"""courier: add online_until column

Revision ID: 0039_courier_online_until
Revises: 0038_plan_price_monthly_annual
Create Date: 2026-07-08
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "couriers",
        sa.Column("online_until", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("couriers", "online_until")
