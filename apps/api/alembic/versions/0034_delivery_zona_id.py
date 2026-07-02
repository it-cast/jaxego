"""Add zona_id to deliveries.

Revision ID: 0034_delivery_zona_id
Revises: 0033_courier_zona
Create Date: 2026-07-02

Stores the zone containing the delivery dropoff point. Populated on creation
via point-in-polygon check. NULL = area has no zones or point outside all zones.
Also saves dropoff_lat/dropoff_lng if missing from prior deliveries (schema gap).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0034_delivery_zona_id"
down_revision = "0033_courier_zona"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deliveries",
        sa.Column("zona_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_deliveries_zona_id_zonas",
        "deliveries",
        "zonas",
        ["zona_id"],
        ["id"],
        ondelete="SET NULL",
        onupdate="CASCADE",
    )
    op.create_index("ix_deliveries_zona_id", "deliveries", ["zona_id"])


def downgrade() -> None:
    op.drop_index("ix_deliveries_zona_id", table_name="deliveries")
    op.drop_constraint("fk_deliveries_zona_id_zonas", "deliveries", type_="foreignkey")
    op.drop_column("deliveries", "zona_id")
