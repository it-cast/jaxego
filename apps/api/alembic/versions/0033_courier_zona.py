"""Create courier_zonas table.

Revision ID: 0033_courier_zona
Revises: 0032_team_zona
Create Date: 2026-07-02

Courier-level price override per zone. courier_preco_cents takes precedence
over the team_zona default. Unique on (courier_id, zona_id).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0033_courier_zona"
down_revision = "0032_team_zona"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "courier_zonas",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        sa.Column("zona_id", sa.BigInteger(), nullable=False),
        sa.Column("preco_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["area_id"], ["areas.id"], ondelete="RESTRICT", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["courier_id"], ["couriers.id"], ondelete="CASCADE", onupdate="CASCADE"),
        sa.ForeignKeyConstraint(["zona_id"], ["zonas.id"], ondelete="CASCADE", onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("courier_id", "zona_id", name="uq_courier_zonas_courier_zona"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )
    op.create_index("ix_courier_zonas_area_id", "courier_zonas", ["area_id"])
    op.create_index("ix_courier_zonas_courier_id", "courier_zonas", ["courier_id"])
    op.create_index("ix_courier_zonas_zona_id", "courier_zonas", ["zona_id"])


def downgrade() -> None:
    op.drop_index("ix_courier_zonas_zona_id", table_name="courier_zonas")
    op.drop_index("ix_courier_zonas_courier_id", table_name="courier_zonas")
    op.drop_index("ix_courier_zonas_area_id", table_name="courier_zonas")
    op.drop_table("courier_zonas")
