"""Create team_zonas table.

Revision ID: 0032_team_zona
Revises: 0031_zona_table
Create Date: 2026-07-02

Relates a team to a zone with a minimum delivery price (preco_minimo_cents).
Unique on (team_id, zona_id). Cascades on team/zona delete.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0032_team_zona"
down_revision = "0031_zona_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "team_zonas",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("team_id", sa.BigInteger(), nullable=False),
        sa.Column("zona_id", sa.BigInteger(), nullable=False),
        sa.Column("preco_minimo_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["area_id"], ["areas.id"], ondelete="RESTRICT", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE", onupdate="CASCADE"),
        sa.ForeignKeyConstraint(["zona_id"], ["zonas.id"], ondelete="CASCADE", onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "zona_id", name="uq_team_zonas_team_zona"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )
    op.create_index("ix_team_zonas_area_id", "team_zonas", ["area_id"])
    op.create_index("ix_team_zonas_team_id", "team_zonas", ["team_id"])
    op.create_index("ix_team_zonas_zona_id", "team_zonas", ["zona_id"])


def downgrade() -> None:
    op.drop_index("ix_team_zonas_zona_id", table_name="team_zonas")
    op.drop_index("ix_team_zonas_team_id", table_name="team_zonas")
    op.drop_index("ix_team_zonas_area_id", table_name="team_zonas")
    op.drop_table("team_zonas")
