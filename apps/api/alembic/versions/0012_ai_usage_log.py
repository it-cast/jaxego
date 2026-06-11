"""ai_usage_log: global LLM usage rail (Phase 14 — T-02 / REQ-053 / D-03 / ADR-001)

Adds the `ai_usage_log` table — the observability rail for the plugable LLM infra
(INFRA ONLY; no AI feature is wired in the M1 pilot). It is GLOBAL (ADR-001): NO
`area_id`, like `users` and `audit_log`.

PII discipline (TH-03): the table carries provider/model/task + token/cost/latency
metadata ONLY — never a prompt, completion, or any personal data. `error_kind` is an
exception type name, never a message.

REVERSIBLE (lição da 0008/0009/0010/0011): `downgrade` drops the single table; its
indexes are dropped with it (no explicit drop_index — dropping a backing index first
trips MySQL errno 1553). The revision id is short (≤ 32 — alembic_version VARCHAR(32)).

Revision ID: 0012_ai_usage_log
Revises: 0011_governance_score_ratings
Create Date: 2026-06-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0012_ai_usage_log"
down_revision: str | None = "0011_governance_score_ratings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE_KW = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}


def _dt() -> sa.types.TypeEngine:
    """DATETIME(6) on MySQL, plain DateTime elsewhere (SQLite dev)."""
    return sa.DateTime(timezone=True).with_variant(mysql.DATETIME(fsp=6), "mysql")


def upgrade() -> None:
    # GLOBAL (ADR-001): NO area_id, no FK to areas. One row per LLM call; NO PII.
    op.create_table(
        "ai_usage_log",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("task", sa.String(length=40), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("error_kind", sa.String(length=64), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_usage_log")),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_ai_usage_log_provider"), "ai_usage_log", ["provider"])
    op.create_index(op.f("ix_ai_usage_log_task"), "ai_usage_log", ["task"])
    op.create_index(op.f("ix_ai_usage_log_created_at"), "ai_usage_log", ["created_at"])


def downgrade() -> None:
    # Single table, no FK — drop it; its indexes drop with it (NO explicit drop_index,
    # lição da 0008/0009/0010/0011: dropping a backing index first trips errno 1553).
    op.drop_table("ai_usage_log")
