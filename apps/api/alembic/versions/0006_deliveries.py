"""deliveries: deliveries, delivery_state_transitions (append-only), recipients

Phase 7 (F-03 + RN-019 state machine). Creates the transactional core schema:
`recipients` (PII separate from address, cpf_hash only — D-08), `deliveries`
(area-scoped, 7-state machine, integer-cent money, RN-013 dropoff separation,
opaque `public_token`), and `delivery_state_transitions` (append-only history —
D-04 / RN-012). The append-only triggers replicate migration 0002's audit_log
pattern (`SIGNAL SQLSTATE '45000'`), emitted only on MySQL (LOW-3 dialect guard);
`downgrade` drops the triggers BEFORE the table.

Revision ID: 0006_deliveries
Revises: 0005_area_operable
Create Date: 2026-06-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "0006_deliveries"
down_revision: str | None = "0005_area_operable"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE_KW = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}


def _dt() -> sa.types.TypeEngine:
    """DATETIME(6) on MySQL, plain DateTime elsewhere (SQLite dev)."""
    return sa.DateTime(timezone=True).with_variant(mysql.DATETIME(fsp=6), "mysql")


# Append-only triggers on delivery_state_transitions (RN-012 / D-04). MySQL-only.
_TRG_NO_UPDATE = (
    "CREATE TRIGGER trg_dst_no_update BEFORE UPDATE ON delivery_state_transitions "
    "FOR EACH ROW SIGNAL SQLSTATE '45000' "
    "SET MESSAGE_TEXT = 'delivery_state_transitions is append-only (RN-012)'"
)
_TRG_NO_DELETE = (
    "CREATE TRIGGER trg_dst_no_delete BEFORE DELETE ON delivery_state_transitions "
    "FOR EACH ROW SIGNAL SQLSTATE '45000' "
    "SET MESSAGE_TEXT = 'delivery_state_transitions is append-only (RN-012)'"
)


def upgrade() -> None:
    # --- recipients (PII separate from address; cpf_hash only — D-08) ---
    op.create_table(
        "recipients",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("phone_e164", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("cpf_hash", sa.String(length=64), nullable=True),
        sa.Column("deliveries_count", sa.Integer(), nullable=False),
        sa.Column("refusals_count", sa.Integer(), nullable=False),
        sa.Column("anonymized_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipients")),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            name=op.f("fk_recipients_area_id_areas"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_recipients_area_id"), "recipients", ["area_id"])
    op.create_index("ix_recipients_area_id_cpf_hash", "recipients", ["area_id", "cpf_hash"])

    # --- deliveries (area-scoped; 7-state machine; RN-013 dropoff separation) ---
    op.create_table(
        "deliveries",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("merchant_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=True),
        sa.Column("recipient_id", sa.BigInteger(), nullable=True),
        sa.Column("state", sa.String(length=24), nullable=False),
        sa.Column("dispatch_mode", sa.String(length=16), nullable=False),
        sa.Column("payment_method", sa.String(length=16), nullable=False),
        sa.Column("proof_method", sa.String(length=16), nullable=False),
        # Pickup
        sa.Column("pickup_address", sa.String(length=255), nullable=False),
        sa.Column("pickup_neighborhood", sa.String(length=120), nullable=True),
        sa.Column("pickup_lat", sa.Float(), nullable=True),
        sa.Column("pickup_lng", sa.Float(), nullable=True),
        # Dropoff — FULL address (RN-013: revealed only after pickup)
        sa.Column("dropoff_address", sa.String(length=255), nullable=False),
        sa.Column("dropoff_number", sa.String(length=20), nullable=True),
        sa.Column("dropoff_complement", sa.String(length=120), nullable=True),
        # Dropoff — revealed before pickup (offer): neighborhood + distance
        sa.Column("dropoff_neighborhood_id", sa.BigInteger(), nullable=False),
        sa.Column("dropoff_lat", sa.Float(), nullable=True),
        sa.Column("dropoff_lng", sa.Float(), nullable=True),
        sa.Column("distance_m", sa.Integer(), nullable=True),
        # Money (integer cents)
        sa.Column("estimate_min_cents", sa.Integer(), nullable=True),
        sa.Column("estimate_max_cents", sa.Integer(), nullable=True),
        sa.Column("fee_cents", sa.Integer(), nullable=False),
        # Items / reference
        sa.Column("items_description", sa.String(length=500), nullable=True),
        sa.Column("items_quantity", sa.Integer(), nullable=False),
        sa.Column("declared_value_cents", sa.Integer(), nullable=True),
        sa.Column("reference_number", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("public_token", sa.String(length=32), nullable=False),
        sa.Column("origin", sa.String(length=16), nullable=False),
        # Per-transition timestamps (aware-UTC)
        sa.Column("accepted_at", _dt(), nullable=True),
        sa.Column("collected_at", _dt(), nullable=True),
        sa.Column("delivered_at", _dt(), nullable=True),
        sa.Column("finalized_at", _dt(), nullable=True),
        sa.Column("cancelled_at", _dt(), nullable=True),
        sa.Column("cancel_reason", sa.String(length=255), nullable=True),
        sa.Column("cancel_actor_user_id", sa.BigInteger(), nullable=True),
        sa.Column("anonymized_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deliveries")),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            name=op.f("fk_deliveries_area_id_areas"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            name=op.f("fk_deliveries_merchant_id_merchants"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["courier_id"],
            ["couriers.id"],
            name=op.f("fk_deliveries_courier_id_couriers"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["recipients.id"],
            name=op.f("fk_deliveries_recipient_id_recipients"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["dropoff_neighborhood_id"],
            ["neighborhoods_catalog.id"],
            name=op.f("fk_deliveries_dropoff_neighborhood_id_neighborhoods_catalog"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.UniqueConstraint("public_token", name="uq_deliveries_public_token"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_deliveries_area_id"), "deliveries", ["area_id"])
    op.create_index(op.f("ix_deliveries_merchant_id"), "deliveries", ["merchant_id"])
    op.create_index(op.f("ix_deliveries_courier_id"), "deliveries", ["courier_id"])
    op.create_index(op.f("ix_deliveries_recipient_id"), "deliveries", ["recipient_id"])
    op.create_index(
        op.f("ix_deliveries_dropoff_neighborhood_id"),
        "deliveries",
        ["dropoff_neighborhood_id"],
    )
    op.create_index(
        "ix_deliveries_area_id_merchant_id_created_at",
        "deliveries",
        ["area_id", "merchant_id", "created_at"],
    )
    op.create_index("ix_deliveries_area_id_state", "deliveries", ["area_id", "state"])

    # --- delivery_state_transitions (append-only — D-04 / RN-012) ---
    op.create_table(
        "delivery_state_transitions",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("delivery_id", sa.BigInteger(), nullable=False),
        sa.Column("from_state", sa.String(length=24), nullable=True),
        sa.Column("to_state", sa.String(length=24), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("gps_lat", sa.Float(), nullable=True),
        sa.Column("gps_lng", sa.Float(), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delivery_state_transitions")),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            name=op.f("fk_delivery_state_transitions_area_id_areas"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["delivery_id"],
            ["deliveries.id"],
            name=op.f("fk_delivery_state_transitions_delivery_id_deliveries"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        **_TABLE_KW,
    )
    op.create_index(
        op.f("ix_delivery_state_transitions_area_id"),
        "delivery_state_transitions",
        ["area_id"],
    )
    op.create_index(
        "ix_delivery_state_transitions_delivery_id",
        "delivery_state_transitions",
        ["delivery_id"],
    )

    # --- append-only triggers (RN-012) — MySQL only (LOW-3 dialect guard) ---
    if op.get_bind().dialect.name == "mysql":
        op.execute(_TRG_NO_UPDATE)
        op.execute(_TRG_NO_DELETE)


def downgrade() -> None:
    # Drop the append-only triggers BEFORE the table they guard (MySQL only).
    if op.get_bind().dialect.name == "mysql":
        op.execute("DROP TRIGGER IF EXISTS trg_dst_no_update")
        op.execute("DROP TRIGGER IF EXISTS trg_dst_no_delete")

    # Drop tables in FK-dependency order (children before parents). All three
    # tables of this migration are dropped here, so NO explicit op.drop_index is
    # needed — drop_table removes the table's indexes with it. On MySQL, dropping
    # an index that backs a FK first raises error 1553 ("needed in a foreign key
    # constraint"), so those calls were not only redundant but broke downgrade.
    #
    # Order: delivery_state_transitions (FK→deliveries) → deliveries
    # (FK→recipients) → recipients. neighborhoods_catalog/areas/merchants/couriers
    # belong to earlier migrations and remain.
    op.drop_table("delivery_state_transitions")
    op.drop_table("deliveries")
    op.drop_table("recipients")
