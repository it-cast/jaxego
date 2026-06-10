"""core auth + multi-area: areas, users, area_admins, refresh_tokens, audit_log

Creates the Phase 2 core schema (REQ-001/002/004/005/006/007) plus the
append-only triggers on `audit_log` (RN-012). All tables are utf8mb4 with the
inherited naming convention; FKs are RESTRICT (DRV-002); timestamps are
DATETIME(6) on MySQL. The append-only triggers are MySQL-specific and emitted
only when the bind dialect is MySQL (LOW-3 dialect guard); `downgrade` drops the
triggers before the table.

Revision ID: 0002_core_auth_multiarea
Revises: 0001_baseline
Create Date: 2026-06-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "0002_core_auth_multiarea"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Table defaults for every table created here (utf8mb4 / UTC-friendly).
_TABLE_KW = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}


def _dt() -> sa.types.TypeEngine:
    """DATETIME(6) on MySQL, plain DateTime elsewhere (SQLite dev)."""
    return sa.DateTime(timezone=True).with_variant(mysql.DATETIME(fsp=6), "mysql")


# Append-only triggers (RN-012). MySQL-specific; SQLite uses a different syntax
# and is not the integrity authority — the acceptance test runs against MySQL 8.
_TRIGGER_NO_UPDATE = (
    "CREATE TRIGGER trg_audit_log_no_update BEFORE UPDATE ON audit_log "
    "FOR EACH ROW SIGNAL SQLSTATE '45000' "
    "SET MESSAGE_TEXT = 'audit_log is append-only (RN-012)'"
)
_TRIGGER_NO_DELETE = (
    "CREATE TRIGGER trg_audit_log_no_delete BEFORE DELETE ON audit_log "
    "FOR EACH ROW SIGNAL SQLSTATE '45000' "
    "SET MESSAGE_TEXT = 'audit_log is append-only (RN-012)'"
)


def upgrade() -> None:
    # --- areas (tenant boundary) ---
    op.create_table(
        "areas",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("codename", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("deleted_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_areas")),
        sa.UniqueConstraint("codename", name=op.f("uq_areas_codename")),
        **_TABLE_KW,
    )

    # --- users (GLOBAL — no area_id) ---
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("cpf", sa.String(length=11), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("platform_role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("failed_attempts", sa.Integer(), nullable=False),
        sa.Column("first_failed_at", _dt(), nullable=True),
        sa.Column("locked_until", _dt(), nullable=True),
        sa.Column("totp_secret", sa.String(length=64), nullable=True),
        sa.Column("totp_required", sa.Boolean(), nullable=False),
        sa.Column("totp_enrolled", sa.Boolean(), nullable=False),
        sa.Column("totp_last_window", sa.BigInteger(), nullable=True),
        sa.Column("deleted_at", _dt(), nullable=True),
        sa.Column("anonymized_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        sa.UniqueConstraint("cpf", name=op.f("uq_users_cpf")),
        **_TABLE_KW,
    )

    # --- area_admins (area-scoped membership) ---
    op.create_table(
        "area_admins",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_area_admins")),
        sa.ForeignKeyConstraint(
            ["area_id"], ["areas.id"],
            name=op.f("fk_area_admins_area_id_areas"),
            ondelete="RESTRICT", onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_area_admins_user_id_users"),
            ondelete="RESTRICT", onupdate="RESTRICT",
        ),
        sa.UniqueConstraint("area_id", "user_id", name="uq_area_admins_area_id_user_id"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_area_admins_area_id"), "area_admins", ["area_id"])
    op.create_index(op.f("ix_area_admins_user_id"), "area_admins", ["user_id"])

    # --- refresh_tokens (hash only) ---
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("family_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", _dt(), nullable=False),
        sa.Column("rotated_at", _dt(), nullable=True),
        sa.Column("revoked_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_refresh_tokens_token_hash")),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"])
    op.create_index(op.f("ix_refresh_tokens_family_id"), "refresh_tokens", ["family_id"])

    # --- audit_log (GLOBAL, append-only) ---
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("area_id", sa.BigInteger(), nullable=True),
        sa.Column("before", sa.JSON(), nullable=True),
        sa.Column("after", sa.JSON(), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("cross_area_bypass", sa.Boolean(), nullable=False),
        sa.Column("created_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log")),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_audit_log_actor_user_id"), "audit_log", ["actor_user_id"])
    op.create_index(op.f("ix_audit_log_action"), "audit_log", ["action"])
    op.create_index(op.f("ix_audit_log_area_id"), "audit_log", ["area_id"])

    # --- append-only triggers (RN-012) — MySQL only (LOW-3 dialect guard) ---
    if op.get_bind().dialect.name == "mysql":
        op.execute(_TRIGGER_NO_UPDATE)
        op.execute(_TRIGGER_NO_DELETE)


def downgrade() -> None:
    # Drop triggers BEFORE the table they guard (MySQL only).
    if op.get_bind().dialect.name == "mysql":
        op.execute("DROP TRIGGER IF EXISTS trg_audit_log_no_update")
        op.execute("DROP TRIGGER IF EXISTS trg_audit_log_no_delete")

    op.drop_index(op.f("ix_audit_log_area_id"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_action"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_actor_user_id"), table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index(op.f("ix_refresh_tokens_family_id"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index(op.f("ix_area_admins_user_id"), table_name="area_admins")
    op.drop_index(op.f("ix_area_admins_area_id"), table_name="area_admins")
    op.drop_table("area_admins")

    op.drop_table("users")
    op.drop_table("areas")
