"""proofs, tracking, notifications, direct payments (Phase 9 — F-06)

Aggregates every Phase 9 table: `delivery_proofs` (T-03), `delivery_locations` (T-06),
`notifications` + `push_subscriptions` (T-09), `direct_payment_confirmations` +
`payment_disputes` (T-09). Also adds `deliveries.cancel_cost_cents` (T-04 / RN-004).

REVERSIBLE (lição da 0006): `downgrade` drops tables in FK-dependency order
(children before parents) and does NOT call `op.drop_index` on indexes that back a
table being dropped (`drop_table` removes them, and dropping a FK-backing index first
trips MySQL errno 1553). No append-only triggers here (none of these tables is
immutable — that pattern is for delivery_state_transitions / audit_log).

Revision ID: 0008_proofs_tracking_notif
Revises: 0007_dispatch_favorites_blocks
Create Date: 2026-06-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0008_proofs_tracking_notif"
down_revision: str | None = "0007_dispatch_favorites_blocks"
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


def _delivery_fk(table: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        ["delivery_id"],
        ["deliveries.id"],
        name=op.f(f"fk_{table}_delivery_id_deliveries"),
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )


def upgrade() -> None:
    # --- deliveries.cancel_cost_cents (RN-004 — T-04) ---
    op.add_column(
        "deliveries",
        sa.Column("cancel_cost_cents", sa.Integer(), nullable=False, server_default="0"),
    )

    # --- delivery_proofs (T-03) ---
    op.create_table(
        "delivery_proofs",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("delivery_id", sa.BigInteger(), nullable=False),
        sa.Column("proof_kind", sa.String(length=16), nullable=False),
        sa.Column("method", sa.String(length=16), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("geofence_ok", sa.Boolean(), nullable=False),
        sa.Column("low_confidence", sa.Boolean(), nullable=False),
        sa.Column("gps_lat", sa.Float(), nullable=True),
        sa.Column("gps_lng", sa.Float(), nullable=True),
        sa.Column("distance_m", sa.Float(), nullable=True),
        sa.Column("refusal_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delivery_proofs")),
        _area_fk("delivery_proofs"),
        _delivery_fk("delivery_proofs"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_delivery_proofs_area_id"), "delivery_proofs", ["area_id"])
    op.create_index("ix_delivery_proofs_delivery_id", "delivery_proofs", ["delivery_id"])

    # --- delivery_locations (T-06) ---
    op.create_table(
        "delivery_locations",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("delivery_id", sa.BigInteger(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("recorded_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delivery_locations")),
        _area_fk("delivery_locations"),
        _delivery_fk("delivery_locations"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_delivery_locations_area_id"), "delivery_locations", ["area_id"])
    op.create_index(
        "ix_delivery_locations_delivery_id_recorded_at",
        "delivery_locations",
        ["delivery_id", "recorded_at"],
    )
    op.create_index("ix_delivery_locations_recorded_at", "delivery_locations", ["recorded_at"])

    # --- notifications (T-09) ---
    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("delivery_id", sa.BigInteger(), nullable=False),
        sa.Column("moment", sa.String(length=16), nullable=False),
        sa.Column("channel", sa.String(length=8), nullable=False),
        sa.Column("status", sa.String(length=8), nullable=False),
        sa.Column("created_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
        _area_fk("notifications"),
        _delivery_fk("notifications"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_notifications_area_id"), "notifications", ["area_id"])
    op.create_index("ix_notifications_delivery_id", "notifications", ["delivery_id"])

    # --- push_subscriptions (T-09) ---
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("delivery_id", sa.BigInteger(), nullable=True),
        sa.Column("endpoint", sa.String(length=512), nullable=False),
        sa.Column("keys_json", sa.Text(), nullable=False),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_push_subscriptions")),
        _area_fk("push_subscriptions"),
        _delivery_fk("push_subscriptions"),
        sa.UniqueConstraint("endpoint", name="uq_push_subscriptions_endpoint"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_push_subscriptions_area_id"), "push_subscriptions", ["area_id"])
    op.create_index("ix_push_subscriptions_user_id", "push_subscriptions", ["user_id"])

    # --- direct_payment_confirmations (T-09) ---
    op.create_table(
        "direct_payment_confirmations",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("delivery_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_direct_payment_confirmations")),
        _area_fk("direct_payment_confirmations"),
        _delivery_fk("direct_payment_confirmations"),
        sa.ForeignKeyConstraint(
            ["courier_id"],
            ["couriers.id"],
            name=op.f("fk_direct_payment_confirmations_courier_id_couriers"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        **_TABLE_KW,
    )
    op.create_index(
        op.f("ix_direct_payment_confirmations_area_id"),
        "direct_payment_confirmations",
        ["area_id"],
    )
    op.create_index(
        "ix_direct_payment_confirmations_delivery_id",
        "direct_payment_confirmations",
        ["delivery_id"],
    )

    # --- payment_disputes (T-09) ---
    op.create_table(
        "payment_disputes",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("delivery_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("opened_at", _dt(), nullable=False),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_disputes")),
        _area_fk("payment_disputes"),
        _delivery_fk("payment_disputes"),
        sa.ForeignKeyConstraint(
            ["courier_id"],
            ["couriers.id"],
            name=op.f("fk_payment_disputes_courier_id_couriers"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_payment_disputes_area_id"), "payment_disputes", ["area_id"])
    op.create_index("ix_payment_disputes_delivery_id", "payment_disputes", ["delivery_id"])


def downgrade() -> None:
    # Drop in FK-dependency order (children of deliveries/couriers first). NO explicit
    # drop_index — drop_table removes the table's indexes with it; dropping an index
    # that backs a FK first trips MySQL errno 1553 (lição da 0006).
    op.drop_table("payment_disputes")
    op.drop_table("direct_payment_confirmations")
    op.drop_table("push_subscriptions")
    op.drop_table("notifications")
    op.drop_table("delivery_locations")
    op.drop_table("delivery_proofs")
    op.drop_column("deliveries", "cancel_cost_cents")
