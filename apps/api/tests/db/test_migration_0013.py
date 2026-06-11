"""Migration 0013 reversibility — MySQL acceptance test (Phase 15 — T-01).

Marked `@pytest.mark.mysql`: requires a LIVE MySQL 8. Asserts that upgrade →
downgrade → upgrade round-trips cleanly for the back-office financial tables
(`platform_invoices`, `invoice_line_items`, `withdrawals`, `dispute_blocks`) — created
on upgrade, removed on downgrade (children-first, no orphaned index / errno 1553),
recreated on re-upgrade. Skipped by default in dev (`-m "not mysql"`); the orchestrator
runs it against real MySQL.

    uv run pytest -m mysql tests/db/test_migration_0013.py -x
"""

from __future__ import annotations

import pytest
from alembic import command
from alembic.config import Config

pytestmark = pytest.mark.mysql

_TABLES = {
    "platform_invoices",
    "invoice_line_items",
    "withdrawals",
    "dispute_blocks",
}
_DISPUTE_COLUMNS = {"decision", "decided_at", "decided_by", "adjustment_cents"}


def _alembic_cfg() -> Config:
    """Alembic config pointed at the configured DATABASE_URL (sync driver)."""
    from app.core.config import settings

    cfg = Config("alembic.ini")
    url = settings.database_url.replace("+aiomysql", "+pymysql").replace("+asyncmy", "+pymysql")
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


@pytest.mark.mysql
def test_migration_0013_round_trips() -> None:
    """upgrade head → downgrade -1 → upgrade head leaves the Phase 15 schema present."""
    import sqlalchemy as sa

    cfg = _alembic_cfg()

    command.upgrade(cfg, "head")
    command.downgrade(cfg, "0012_ai_usage_log")

    from app.core.config import settings

    url = settings.database_url.replace("+aiomysql", "+pymysql").replace("+asyncmy", "+pymysql")
    engine = sa.create_engine(url)
    insp = sa.inspect(engine)
    present = set(insp.get_table_names())
    assert not (_TABLES & present), "Phase 15 tables survived downgrade"
    dispute_cols = {c["name"] for c in insp.get_columns("payment_disputes")}
    assert not (_DISPUTE_COLUMNS & dispute_cols), "decision columns survived downgrade"

    command.upgrade(cfg, "head")
    insp = sa.inspect(engine)
    present = set(insp.get_table_names())
    assert _TABLES <= present, "Phase 15 tables missing after re-upgrade"
    dispute_cols = {c["name"] for c in insp.get_columns("payment_disputes")}
    assert _DISPUTE_COLUMNS <= dispute_cols, "decision columns missing after re-upgrade"
    engine.dispose()
