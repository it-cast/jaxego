"""Add ativo column to courier_zonas.

Revision ID: 0036_courier_zona_ativo
Revises: 0035_delivery_dropoff_reference
Create Date: 2026-07-03

Couriers can now mark which zones they serve. Existing rows default to True
(active). New zones link to all couriers with ativo=False (opt-in required).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0036_courier_zona_ativo"
down_revision = "0035_delivery_dropoff_reference"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "courier_zonas",
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("courier_zonas", "ativo")
