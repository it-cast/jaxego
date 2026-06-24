"""0018 — drop courier_score_snapshots and score_weights.

Score is now calculated in real-time from courier_ratings. These tables
are no longer read by any code.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018_drop_score_tables"
down_revision: str | None = "0017_receipt_method"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("courier_score_snapshots")
    op.drop_table("score_weights")


def downgrade() -> None:
    op.create_table(
        "score_weights",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("component", sa.String(32), nullable=False),
        sa.Column("weight", sa.Numeric(5, 3), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("component", name="uq_score_weights_component"),
    )
    op.create_table(
        "courier_score_snapshots",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_score", sa.Numeric(6, 2), nullable=False),
        sa.Column("level", sa.String(16), nullable=False),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["area_id"], ["areas.id"]),
        sa.ForeignKeyConstraint(["courier_id"], ["couriers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("courier_id", "snapshot_date", name="uq_courier_score_snapshots_courier_date"),
    )
