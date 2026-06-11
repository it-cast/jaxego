"""Migration 0008 is reversible against LIVE MySQL 8 (@pytest.mark.mysql).

Drives the real alembic chain: `upgrade head` → `downgrade -1` → `upgrade head`, and
asserts the five Phase-9 tables (delivery_proofs, delivery_locations, notifications,
push_subscriptions, direct_payment_confirmations, payment_disputes) + the
`deliveries.cancel_cost_cents` column appear after upgrade, vanish after downgrade,
and come back — proving the `downgrade` is symmetric and does not trip the
FK-backing-index errno 1553 that broke the 0006 downgrade (lição da 0006). Skipped in
dev via `-m "not mysql"` (the chain has MySQL-only DDL). Run live:

    cd apps/api && uv run pytest -m mysql tests/db/test_migration_0008.py

The test runs alembic in-process via `command.upgrade/downgrade` with a Config
pointed at `settings.database_url`. It restores the DB to `head` in teardown so the
rest of the live suite sees a fully-migrated schema.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from app.core.config import settings
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.mysql

_NEW_TABLES = (
    "delivery_proofs",
    "delivery_locations",
    "notifications",
    "push_subscriptions",
    "direct_payment_confirmations",
    "payment_disputes",
)


def _sync_url() -> str:
    """The MySQL URL with a sync driver for inspect() (asyncmy → pymysql)."""
    return settings.database_url.replace("+asyncmy", "+pymysql").replace("+aiomysql", "+pymysql")


def _alembic_config() -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    return cfg


def _tables() -> set[str]:
    engine = create_engine(_sync_url())
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def _columns(table: str) -> set[str]:
    engine = create_engine(_sync_url())
    try:
        return {c["name"] for c in inspect(engine).get_columns(table)}
    finally:
        engine.dispose()


@pytest.fixture
def at_head() -> Iterator[Config]:
    """Ensure head before and after (restore the live schema for the rest of the suite)."""
    cfg = _alembic_config()
    command.upgrade(cfg, "head")
    yield cfg
    command.upgrade(cfg, "head")


def test_0008_upgrade_creates_tables(at_head: Config) -> None:
    tables = _tables()
    for t in _NEW_TABLES:
        assert t in tables, t
    assert "cancel_cost_cents" in _columns("deliveries")


def test_0008_downgrade_then_upgrade_is_reversible(at_head: Config) -> None:
    # Down one revision (removes 0008).
    command.downgrade(at_head, "-1")
    tables = _tables()
    for t in _NEW_TABLES:
        assert t not in tables, t
    assert "cancel_cost_cents" not in _columns("deliveries")

    # Back up — the symmetric upgrade restores everything (errno 1553 would have
    # broken the downgrade if a FK-backing index were dropped first).
    command.upgrade(at_head, "head")
    tables = _tables()
    for t in _NEW_TABLES:
        assert t in tables, t
    assert "cancel_cost_cents" in _columns("deliveries")
