"""Create zonas table and drop boundary from areas.

Revision ID: 0031_zona_table
Revises: 0030_scheduled_delivery
Create Date: 2026-07-02

Zones replace the per-area polygon: admin_area now manages zones (sub-divisions
of an area each with its own GeoJSON boundary) instead of a single area-level
polygon. The `boundary` column is dropped from `areas`; `zonas` table is created
with area_id FK, name, and boundary (JSON).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0031_zona_table"
down_revision = "0030_scheduled_delivery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "zonas",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("boundary", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["area_id"], ["areas.id"], ondelete="RESTRICT", onupdate="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_zonas_area_id", "zonas", ["area_id"])
    op.drop_column("areas", "boundary")


def downgrade() -> None:
    op.add_column("areas", sa.Column("boundary", sa.JSON(), nullable=True))
    op.drop_index("ix_zonas_area_id", table_name="zonas")
    op.drop_table("zonas")
