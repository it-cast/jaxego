"""public API keys + idempotency + outbound webhooks (Phase 12 — REQ-041/042/043)

Adds the public-API surface:
- `api_keys` (area-scoped integrator key — argon2id `secret_hash`, public `key_id`,
  soft-revoke `revoked_at`).
- `api_idempotency_keys` (24h response snapshot keyed by `(api_key_id, idempotency_key)`
  — request_hash + cached response, FK RESTRICT to `api_keys`).
- `webhook_endpoints` (one per area — URL + signing secret + subscribed events).
- `webhook_deliveries` (one attempt-set per event — ULID `event_id`, payload, attempts,
  next_retry_at; FK RESTRICT to `webhook_endpoints` and `deliveries`).
- `merchants.external_ref` (the integrator's store id — Phase 12 / D-03; unique per area).

REVERSIBLE (lição da 0006/0008/0009): `downgrade` drops tables CHILDREN-FIRST
(`webhook_deliveries` before `webhook_endpoints`, `api_idempotency_keys` before
`api_keys`) and does NOT call `op.drop_index` on indexes that back a dropped table
(drop_table removes them; dropping a FK-backing index first trips MySQL errno 1553).
The merchant column + its unique constraint are dropped last. The revision id is
short (24 chars ≤ 32 — alembic_version VARCHAR(32) lição).

Revision ID: 0010_public_api_webhooks
Revises: 0009_safe2pay_billing_escrow
Create Date: 2026-06-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0010_public_api_webhooks"
down_revision: str | None = "0009_safe2pay_billing_escrow"
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
    # --- merchants.external_ref (Phase 12 / D-03 — integrator store id, unique per area) ---
    op.add_column("merchants", sa.Column("external_ref", sa.String(length=120), nullable=True))
    op.create_unique_constraint(
        "uq_merchants_area_id_external_ref", "merchants", ["area_id", "external_ref"]
    )

    # --- api_keys (area-scoped integrator key — argon2id hash, public key_id) ---
    op.create_table(
        "api_keys",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("key_id", sa.String(length=32), nullable=False),
        sa.Column("secret_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("scopes", sa.String(length=255), nullable=False),
        sa.Column("revoked_at", _dt(), nullable=True),
        sa.Column("last_used_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_keys")),
        _area_fk("api_keys"),
        sa.UniqueConstraint("key_id", name="uq_api_keys_key_id"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_api_keys_area_id"), "api_keys", ["area_id"])
    op.create_index("ix_api_keys_area_id_created_at", "api_keys", ["area_id", "created_at"])

    # --- api_idempotency_keys (24h response snapshot — FK RESTRICT to api_keys) ---
    op.create_table(
        "api_idempotency_keys",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("api_key_id", sa.BigInteger(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.Text(), nullable=False),
        sa.Column("delivery_id", sa.BigInteger(), nullable=True),
        sa.Column("expires_at", _dt(), nullable=False),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_idempotency_keys")),
        _area_fk("api_idempotency_keys"),
        sa.ForeignKeyConstraint(
            ["api_key_id"],
            ["api_keys.id"],
            name=op.f("fk_api_idempotency_keys_api_key_id_api_keys"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.UniqueConstraint(
            "api_key_id", "idempotency_key", name="uq_api_idempotency_keys_apikey_key"
        ),
        **_TABLE_KW,
    )
    op.create_index(
        op.f("ix_api_idempotency_keys_area_id"), "api_idempotency_keys", ["area_id"]
    )
    op.create_index(
        "ix_api_idempotency_keys_expires_at", "api_idempotency_keys", ["expires_at"]
    )

    # --- webhook_endpoints (one per area — URL + signing secret + events) ---
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("secret", sa.String(length=128), nullable=False),
        sa.Column("events", sa.String(length=512), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_webhook_endpoints")),
        _area_fk("webhook_endpoints"),
        sa.UniqueConstraint("area_id", name="uq_webhook_endpoints_area_id"),
        **_TABLE_KW,
    )
    # NOTE: the area_id UNIQUE already indexes area_id; no separate ix_ needed.

    # --- webhook_deliveries (one attempt-set per event — FK to endpoints + deliveries) ---
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("endpoint_id", sa.BigInteger(), nullable=False),
        sa.Column("delivery_id", sa.BigInteger(), nullable=False),
        sa.Column("event_id", sa.String(length=26), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_retry_at", _dt(), nullable=True),
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column("delivered_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_webhook_deliveries")),
        _area_fk("webhook_deliveries"),
        sa.ForeignKeyConstraint(
            ["endpoint_id"],
            ["webhook_endpoints.id"],
            name=op.f("fk_webhook_deliveries_endpoint_id_webhook_endpoints"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["delivery_id"],
            ["deliveries.id"],
            name=op.f("fk_webhook_deliveries_delivery_id_deliveries"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.UniqueConstraint("event_id", name="uq_webhook_deliveries_event_id"),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_webhook_deliveries_area_id"), "webhook_deliveries", ["area_id"])
    op.create_index(
        "ix_webhook_deliveries_status_next_retry_at",
        "webhook_deliveries",
        ["status", "next_retry_at"],
    )
    op.create_index(
        "ix_webhook_deliveries_endpoint_id", "webhook_deliveries", ["endpoint_id"]
    )


def downgrade() -> None:
    # Drop tables CHILDREN-FIRST. NO explicit drop_index — drop_table removes the
    # table's indexes with it; dropping a FK-backing index first trips MySQL errno 1553
    # (lição da 0006/0008/0009).
    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_endpoints")
    op.drop_table("api_idempotency_keys")
    op.drop_table("api_keys")

    # Merchant column last: drop the unique constraint that backs it, then the column.
    op.drop_constraint("uq_merchants_area_id_external_ref", "merchants", type_="unique")
    op.drop_column("merchants", "external_ref")
