"""governance: score snapshots + ratings + suspension appeals + revenue share (Phase 13)

Adds the governance surface (REQ-020/033/045/046/047):
- `score_weights` (GLOBAL seed — parametrised component weights, DRV-009; NOT area-scoped,
  the weight table is platform catalog like `subscription_plans`).
- `courier_score_snapshots` (area-scoped — one snapshot per (courier, day); `components` JSON
  carries name/raw/weight/contribution; `level` enum probation/bronze/prata/ouro/diamante).
- `courier_ratings` (area-scoped — store rates courier after FINALIZADA, 1-5 + comment,
  UNIQUE per `delivery_id` → one rating per delivery).
- `suspension_appeals` (area-scoped — subject_type/subject_id + sla_due_at + decision
  upheld/overturned; the suspension window with its SLA, reused by the SLA reversion job).
- `area_revenue_share` (area-scoped — parametrised config %, seed-editable, effective_from
  versioned; NO money moves here — DEC-004/D-07).

REVERSIBLE (lição da 0008/0009/0010): `downgrade` drops tables CHILDREN-FIRST and does NOT
call `op.drop_index` on indexes backing a dropped table (drop_table removes them; dropping a
FK-backing index first trips MySQL errno 1553). The revision id is short (≤ 32 —
alembic_version VARCHAR(32) lição).

Revision ID: 0011_governance_score_ratings
Revises: 0010_public_api_webhooks
Create Date: 2026-06-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0011_governance_score_ratings"
down_revision: str | None = "0010_public_api_webhooks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE_KW = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}


def _dt() -> sa.types.TypeEngine:
    """DATETIME(6) on MySQL, plain DateTime elsewhere (SQLite dev)."""
    return sa.DateTime(timezone=True).with_variant(mysql.DATETIME(fsp=6), "mysql")


def _area_fk(table: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        ["area_id"],
        ["areas.id"],
        name=op.f(f"fk_{table}_area_id_areas"),
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )


def upgrade() -> None:
    # --- score_weights (GLOBAL seed — parametrised component weights, DRV-009) ---
    op.create_table(
        "score_weights",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("component", sa.String(length=40), nullable=False),
        sa.Column("weight", sa.Numeric(6, 4), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_score_weights")),
        sa.UniqueConstraint("component", name="uq_score_weights_component"),
        **_TABLE_KW,
    )

    # --- courier_score_snapshots (area-scoped — one per courier per day) ---
    op.create_table(
        "courier_score_snapshots",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_score", sa.Numeric(6, 2), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_courier_score_snapshots")),
        _area_fk("courier_score_snapshots"),
        sa.ForeignKeyConstraint(
            ["courier_id"],
            ["couriers.id"],
            name=op.f("fk_courier_score_snapshots_courier_id_couriers"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        # One snapshot per (courier, day) — idempotent job (1/dia/courier).
        sa.UniqueConstraint(
            "courier_id", "snapshot_date", name="uq_courier_score_snapshots_courier_date"
        ),
        **_TABLE_KW,
    )
    op.create_index(
        op.f("ix_courier_score_snapshots_area_id"), "courier_score_snapshots", ["area_id"]
    )
    op.create_index(
        "ix_courier_score_snapshots_courier_date",
        "courier_score_snapshots",
        ["courier_id", "snapshot_date"],
    )

    # --- courier_ratings (area-scoped — store rates courier post-FINALIZADA) ---
    op.create_table(
        "courier_ratings",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("delivery_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        sa.Column("merchant_id", sa.BigInteger(), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_courier_ratings")),
        _area_fk("courier_ratings"),
        sa.ForeignKeyConstraint(
            ["delivery_id"],
            ["deliveries.id"],
            name=op.f("fk_courier_ratings_delivery_id_deliveries"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["courier_id"],
            ["couriers.id"],
            name=op.f("fk_courier_ratings_courier_id_couriers"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            name=op.f("fk_courier_ratings_merchant_id_merchants"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        # One rating per delivery (D-03 — append, 1 por entrega).
        sa.UniqueConstraint("delivery_id", name="uq_courier_ratings_delivery_id"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_courier_ratings_area_id"), "courier_ratings", ["area_id"])
    op.create_index("ix_courier_ratings_courier_id", "courier_ratings", ["courier_id"])

    # --- suspension_appeals (area-scoped — suspension window + SLA + decision) ---
    op.create_table(
        "suspension_appeals",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("subject_type", sa.String(length=16), nullable=False),
        sa.Column("subject_id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("opened_at", _dt(), nullable=False),
        sa.Column("sla_due_at", _dt(), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=True),
        sa.Column("decided_at", _dt(), nullable=True),
        sa.Column("decided_by", sa.BigInteger(), nullable=True),
        sa.Column("reverted_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_suspension_appeals")),
        _area_fk("suspension_appeals"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_suspension_appeals_area_id"), "suspension_appeals", ["area_id"])
    op.create_index(
        "ix_suspension_appeals_subject",
        "suspension_appeals",
        ["subject_type", "subject_id"],
    )
    # The SLA sweep finds undecided appeals past due — index decision+sla_due_at.
    op.create_index(
        "ix_suspension_appeals_decision_sla",
        "suspension_appeals",
        ["decision", "sla_due_at"],
    )

    # --- area_revenue_share (area-scoped — parametrised config %, effective_from versioned) ---
    op.create_table(
        "area_revenue_share",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("share_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("effective_from", _dt(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_area_revenue_share")),
        _area_fk("area_revenue_share"),
        sa.UniqueConstraint(
            "area_id", "effective_from", name="uq_area_revenue_share_area_effective"
        ),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_area_revenue_share_area_id"), "area_revenue_share", ["area_id"])


def downgrade() -> None:
    # Drop CHILDREN-FIRST. NO explicit drop_index — drop_table removes the table's
    # indexes with it; dropping a FK-backing index first trips MySQL errno 1553
    # (lição da 0008/0009/0010). score_weights has no FK; order among siblings is free.
    op.drop_table("area_revenue_share")
    op.drop_table("suspension_appeals")
    op.drop_table("courier_ratings")
    op.drop_table("courier_score_snapshots")
    op.drop_table("score_weights")
