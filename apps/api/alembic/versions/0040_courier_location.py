"""courier: add lat/lng/location_at for dispatch proximity ranking.

Revision ID: 0040
Revises: 0039
Create Date: 2026-07-08
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0040"
down_revision = "0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("couriers", sa.Column("lat", sa.Float(), nullable=True))
    op.add_column("couriers", sa.Column("lng", sa.Float(), nullable=True))
    op.add_column(
        "couriers",
        sa.Column("location_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("couriers", "location_at")
    op.drop_column("couriers", "lng")
    op.drop_column("couriers", "lat")
