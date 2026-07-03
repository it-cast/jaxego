"""add dropoff_reference to deliveries

Revision ID: 0035
Revises: 0034
Create Date: 2026-07-03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0035_delivery_dropoff_reference"
down_revision = "0034_delivery_zona_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deliveries",
        sa.Column("dropoff_reference", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("deliveries", "dropoff_reference")
