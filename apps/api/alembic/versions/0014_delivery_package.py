"""0014 — package weight + dimensions on deliveries (MG-1).

Adds optional structured package data (`weight_g`, `length_cm`, `width_cm`,
`height_cm`) so the store can declare size/weight (multi-vehicle parity). All
nullable — existing deliveries and the text `items_description` keep working.
Reversible: downgrade drops the four columns.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_delivery_package"
down_revision: str | None = "0013_financeiro_back_office"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("deliveries", sa.Column("weight_g", sa.Integer(), nullable=True))
    op.add_column("deliveries", sa.Column("length_cm", sa.Integer(), nullable=True))
    op.add_column("deliveries", sa.Column("width_cm", sa.Integer(), nullable=True))
    op.add_column("deliveries", sa.Column("height_cm", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("deliveries", "height_cm")
    op.drop_column("deliveries", "width_cm")
    op.drop_column("deliveries", "length_cm")
    op.drop_column("deliveries", "weight_g")
