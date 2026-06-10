"""merchants + plans: subscription_plans, merchants, merchant_users, merchant_subscriptions

Adds the Phase 4 store-onboarding schema (REQ-008/009/006), reusing the Phase 2
conventions: utf8mb4 tables, the inherited naming convention, FKs RESTRICT
(DRV-002), DATETIME(6) on MySQL. `merchants` and `merchant_subscriptions` are
area-scoped (area_id BIGINT NOT NULL + FK to areas); `subscription_plans` and
`merchant_users` are global association/catalog tables.

RN-011 uniqueness is enforced by a composite UNIQUE (account_type, document) plus
single UNIQUE on phone_e164 and email.

Revision ID: 0003_merchants_plans
Revises: 0002_core_auth_multiarea
Create Date: 2026-06-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "0003_merchants_plans"
down_revision: str | None = "0002_core_auth_multiarea"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE_KW = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}


def _dt() -> sa.types.TypeEngine:
    """DATETIME(6) on MySQL, plain DateTime elsewhere (SQLite dev)."""
    return sa.DateTime(timezone=True).with_variant(mysql.DATETIME(fsp=6), "mysql")


def upgrade() -> None:
    # --- subscription_plans (GLOBAL catalog — values are SEED data, DRV-009) ---
    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("deliveries_per_month", sa.Integer(), nullable=False),
        sa.Column("fee_cents", sa.Integer(), nullable=False),
        sa.Column("is_free", sa.Boolean(), nullable=False),
        sa.Column("is_unlimited", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscription_plans")),
        sa.UniqueConstraint("code", name=op.f("uq_subscription_plans_code")),
        **_TABLE_KW,
    )

    # --- merchants (AREA-SCOPED — area_id NOT NULL FK to areas) ---
    op.create_table(
        "merchants",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("account_type", sa.String(length=8), nullable=False),
        sa.Column("document", sa.String(length=20), nullable=False),
        sa.Column("trade_name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("phone_e164", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("receita_validated", sa.Boolean(), nullable=False),
        sa.Column("revalidation_attempts", sa.Integer(), nullable=False),
        sa.Column("next_revalidation_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_merchants")),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            name=op.f("fk_merchants_area_id_areas"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.UniqueConstraint("account_type", "document", name="uq_merchants_account_type_document"),
        sa.UniqueConstraint("phone_e164", name=op.f("uq_merchants_phone_e164")),
        sa.UniqueConstraint("email", name=op.f("uq_merchants_email")),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_merchants_area_id"), "merchants", ["area_id"])

    # --- merchant_users (GLOBAL association) ---
    op.create_table(
        "merchant_users",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("merchant_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_merchant_users")),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            name=op.f("fk_merchant_users_merchant_id_merchants"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_merchant_users_user_id_users"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.UniqueConstraint("merchant_id", "user_id", name="uq_merchant_users_merchant_id_user_id"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_merchant_users_merchant_id"), "merchant_users", ["merchant_id"])
    op.create_index(op.f("ix_merchant_users_user_id"), "merchant_users", ["user_id"])

    # --- merchant_subscriptions (AREA-SCOPED) ---
    op.create_table(
        "merchant_subscriptions",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("merchant_id", sa.BigInteger(), nullable=False),
        sa.Column("plan_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_merchant_subscriptions")),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            name=op.f("fk_merchant_subscriptions_area_id_areas"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            name=op.f("fk_merchant_subscriptions_merchant_id_merchants"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["subscription_plans.id"],
            name=op.f("fk_merchant_subscriptions_plan_id_subscription_plans"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        **_TABLE_KW,
    )
    op.create_index(
        op.f("ix_merchant_subscriptions_area_id"), "merchant_subscriptions", ["area_id"]
    )
    op.create_index(
        op.f("ix_merchant_subscriptions_merchant_id"), "merchant_subscriptions", ["merchant_id"]
    )
    op.create_index(
        op.f("ix_merchant_subscriptions_plan_id"), "merchant_subscriptions", ["plan_id"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_merchant_subscriptions_plan_id"), table_name="merchant_subscriptions")
    op.drop_index(
        op.f("ix_merchant_subscriptions_merchant_id"), table_name="merchant_subscriptions"
    )
    op.drop_index(op.f("ix_merchant_subscriptions_area_id"), table_name="merchant_subscriptions")
    op.drop_table("merchant_subscriptions")

    op.drop_index(op.f("ix_merchant_users_user_id"), table_name="merchant_users")
    op.drop_index(op.f("ix_merchant_users_merchant_id"), table_name="merchant_users")
    op.drop_table("merchant_users")

    op.drop_index(op.f("ix_merchants_area_id"), table_name="merchants")
    op.drop_table("merchants")

    op.drop_table("subscription_plans")
