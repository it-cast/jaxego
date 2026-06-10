"""couriers + courier_documents: F-02 courier onboarding + KYC (Phase 5)

Adds the Phase 5 courier-onboarding schema (REQ-013/014/015/019), reusing the
Phase 2/4 conventions: utf8mb4 tables, the inherited naming convention, FKs
RESTRICT (DRV-002), DATETIME(6) on MySQL. Both tables are AREA-SCOPED
(area_id BIGINT NOT NULL + FK to areas) so the admin queue / view-url query can
filter by area in the WHERE clause (TH-03).

F-02 E2 is enforced structurally by the composite UNIQUE (area_id, cpf): a CPF
may onboard in several areas but not twice in the same one.
`courier_documents` carries storage_key/sha256/status/expires_at (RN-021:
anonymized_at/deleted_at nullable from day one) and is indexed on expires_at
(batch expiry sweep, no N+1) and (courier_id, status) (per-courier item list).

All datetime columns are DATETIME(6) UTC (TD-010).

Revision ID: 0004_couriers_kyc
Revises: 0003_merchants_plans
Create Date: 2026-06-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "0004_couriers_kyc"
down_revision: str | None = "0003_merchants_plans"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE_KW = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}


def _dt() -> sa.types.TypeEngine:
    """DATETIME(6) on MySQL, plain DateTime elsewhere (SQLite dev)."""
    return sa.DateTime(timezone=True).with_variant(mysql.DATETIME(fsp=6), "mysql")


def upgrade() -> None:
    # --- couriers (AREA-SCOPED — area_id NOT NULL FK to areas) ---
    op.create_table(
        "couriers",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("cpf", sa.String(length=11), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("phone_e164", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("kyc_level", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("vehicle_type", sa.String(length=16), nullable=False),
        sa.Column("vehicle_plate", sa.String(length=8), nullable=True),
        sa.Column("mei_cnpj", sa.String(length=14), nullable=True),
        sa.Column("mei_pending", sa.Boolean(), nullable=False),
        sa.Column("anonymized_at", _dt(), nullable=True),
        sa.Column("deleted_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_couriers")),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            name=op.f("fk_couriers_area_id_areas"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_couriers_user_id_users"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        # F-02 E2: one CPF per area (not global) — new vínculo per area allowed.
        sa.UniqueConstraint("area_id", "cpf", name="uq_couriers_area_id_cpf"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_couriers_area_id"), "couriers", ["area_id"])
    op.create_index(op.f("ix_couriers_user_id"), "couriers", ["user_id"])

    # --- courier_documents (AREA-SCOPED — per-item KYC status, D-04) ---
    op.create_table(
        "courier_documents",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=True),
        sa.Column("content_type", sa.String(length=64), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("sha256_client", sa.String(length=64), nullable=True),
        sa.Column("reject_reason", sa.String(length=32), nullable=True),
        sa.Column("reject_detail", sa.String(length=500), nullable=True),
        sa.Column("expires_at", _dt(), nullable=True),
        sa.Column("submitted_at", _dt(), nullable=True),
        sa.Column("anonymized_at", _dt(), nullable=True),
        sa.Column("deleted_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_courier_documents")),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            name=op.f("fk_courier_documents_area_id_areas"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["courier_id"],
            ["couriers.id"],
            name=op.f("fk_courier_documents_courier_id_couriers"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_courier_documents_area_id"), "courier_documents", ["area_id"])
    op.create_index(op.f("ix_courier_documents_courier_id"), "courier_documents", ["courier_id"])
    # Batch expiry sweep (CNH/CRLV/MEI) — index on expires_at (no N+1).
    op.create_index(op.f("ix_courier_documents_expires_at"), "courier_documents", ["expires_at"])
    # Per-courier item list by status (admin detail — no N+1).
    op.create_index(
        "ix_courier_documents_courier_id_status",
        "courier_documents",
        ["courier_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_courier_documents_courier_id_status", table_name="courier_documents")
    op.drop_index(op.f("ix_courier_documents_expires_at"), table_name="courier_documents")
    op.drop_index(op.f("ix_courier_documents_courier_id"), table_name="courier_documents")
    op.drop_index(op.f("ix_courier_documents_area_id"), table_name="courier_documents")
    op.drop_table("courier_documents")

    op.drop_index(op.f("ix_couriers_user_id"), table_name="couriers")
    op.drop_index(op.f("ix_couriers_area_id"), table_name="couriers")
    op.drop_table("couriers")
