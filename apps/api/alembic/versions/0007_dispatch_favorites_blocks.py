"""dispatch: merchant_courier_favorites, merchant_courier_blocks (RN-014)

Phase 8 (F-05 dispatch). Two SEPARATE tables (RN-014 / D-06): a store's favorite
couriers (entered FIRST in the cascade, ordered by `priority` — D-01) and a
store's blocked couriers (never offered, private `reason` note). Both are
area-scoped store↔courier pairs with UNIQUE(area_id, merchant_id, courier_id) and
FK RESTRICT (DRV-002), utf8mb4. The (area_id, merchant_id) composite index backs
the candidate-build query (Gate 8 — no table scan). No backfill (new entities).

Revision ID: 0007_dispatch_favorites_blocks
Revises: 0006_deliveries
Create Date: 2026-06-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "0007_dispatch_favorites_blocks"
down_revision: str | None = "0006_deliveries"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE_KW = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}


def _dt() -> sa.types.TypeEngine:
    """DATETIME(6) on MySQL, plain DateTime elsewhere (SQLite dev)."""
    return sa.DateTime(timezone=True).with_variant(mysql.DATETIME(fsp=6), "mysql")


def upgrade() -> None:
    # --- merchant_courier_favorites (RN-014 / D-06 / D-01 priority) ---
    op.create_table(
        "merchant_courier_favorites",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("merchant_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_merchant_courier_favorites")),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            name=op.f("fk_merchant_courier_favorites_area_id_areas"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            name=op.f("fk_merchant_courier_favorites_merchant_id_merchants"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["courier_id"],
            ["couriers.id"],
            name=op.f("fk_merchant_courier_favorites_courier_id_couriers"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.UniqueConstraint(
            "area_id",
            "merchant_id",
            "courier_id",
            name="uq_merchant_courier_favorites_area_merchant_courier",
        ),
        **_TABLE_KW,
    )
    op.create_index(
        op.f("ix_merchant_courier_favorites_area_id"),
        "merchant_courier_favorites",
        ["area_id"],
    )
    op.create_index(
        op.f("ix_merchant_courier_favorites_merchant_id"),
        "merchant_courier_favorites",
        ["merchant_id"],
    )
    op.create_index(
        op.f("ix_merchant_courier_favorites_courier_id"),
        "merchant_courier_favorites",
        ["courier_id"],
    )
    op.create_index(
        "ix_merchant_courier_favorites_area_id_merchant_id",
        "merchant_courier_favorites",
        ["area_id", "merchant_id"],
    )

    # --- merchant_courier_blocks (RN-014 / D-06 — private reason) ---
    op.create_table(
        "merchant_courier_blocks",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("merchant_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_merchant_courier_blocks")),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            name=op.f("fk_merchant_courier_blocks_area_id_areas"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            name=op.f("fk_merchant_courier_blocks_merchant_id_merchants"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["courier_id"],
            ["couriers.id"],
            name=op.f("fk_merchant_courier_blocks_courier_id_couriers"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.UniqueConstraint(
            "area_id",
            "merchant_id",
            "courier_id",
            name="uq_merchant_courier_blocks_area_merchant_courier",
        ),
        **_TABLE_KW,
    )
    op.create_index(
        op.f("ix_merchant_courier_blocks_area_id"),
        "merchant_courier_blocks",
        ["area_id"],
    )
    op.create_index(
        op.f("ix_merchant_courier_blocks_merchant_id"),
        "merchant_courier_blocks",
        ["merchant_id"],
    )
    op.create_index(
        op.f("ix_merchant_courier_blocks_courier_id"),
        "merchant_courier_blocks",
        ["courier_id"],
    )
    op.create_index(
        "ix_merchant_courier_blocks_area_id_merchant_id",
        "merchant_courier_blocks",
        ["area_id", "merchant_id"],
    )


def downgrade() -> None:
    # Drop both tables (no dependents). drop_table removes their indexes with them;
    # dropping an FK-backing index first on MySQL would raise 1553 (see 0006).
    op.drop_table("merchant_courier_blocks")
    op.drop_table("merchant_courier_favorites")
