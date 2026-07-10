"""Move max_concurrent de couriers para areas.config.

Antes: `couriers.max_concurrent` INTEGER NOT NULL DEFAULT 1 — por entregador.
Depois: regra fica em `areas.config['max_entregas_simultaneas']` (JSON) — por área.

A coluna `couriers.max_concurrent` é removida. O campo JSON não requer ALTER TABLE
em `areas` pois a coluna `config` já existe — a validação é feita pelo Pydantic
(`AreaConfig.max_entregas_simultaneas`, default=1).

Revision ID: 0041
Revises: 0040
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("couriers", "max_concurrent")


def downgrade() -> None:
    op.add_column(
        "couriers",
        sa.Column("max_concurrent", sa.Integer(), nullable=False, server_default="1"),
    )
