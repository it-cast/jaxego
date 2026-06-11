"""Migration 0009 is reversible against LIVE MySQL 8 (@pytest.mark.mysql).

Drives the real alembic chain: `upgrade head` → `downgrade -1` → `upgrade head`, and
asserts the three Phase-10 tables (platform_charges, escrow_ledger,
payment_webhook_events) + the `merchant_subscriptions.billing_status` and
`couriers.s2p_recipient_id` columns appear after upgrade, vanish after downgrade, and
come back — proving the `downgrade` is symmetric and does not trip errno 1553 (lição
0006/0008). The revision id is 28 chars (≤ 32 — alembic_version VARCHAR(32) lição).
Skipped in dev via `-m "not mysql"`. Run live:

    cd apps/api && uv run pytest -m mysql tests/db/test_migration_0009.py
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
    "platform_charges",
    "escrow_ledger",
    "payment_webhook_events",
)


def _sync_url() -> str:
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
    cfg = _alembic_config()
    command.upgrade(cfg, "head")
    yield cfg
    command.upgrade(cfg, "head")


def test_0009_upgrade_creates_tables_and_columns(at_head: Config) -> None:
    tables = _tables()
    for t in _NEW_TABLES:
        assert t in tables, t
    assert "billing_status" in _columns("merchant_subscriptions")
    assert "safe2pay_token" in _columns("merchant_subscriptions")
    assert "s2p_recipient_id" in _columns("couriers")


def test_0009_downgrade_then_upgrade_is_reversible(at_head: Config) -> None:
    command.downgrade(at_head, "-1")
    tables = _tables()
    for t in _NEW_TABLES:
        assert t not in tables, t
    assert "billing_status" not in _columns("merchant_subscriptions")
    assert "s2p_recipient_id" not in _columns("couriers")

    command.upgrade(at_head, "head")
    tables = _tables()
    for t in _NEW_TABLES:
        assert t in tables, t
    assert "billing_status" in _columns("merchant_subscriptions")
    assert "s2p_recipient_id" in _columns("couriers")
