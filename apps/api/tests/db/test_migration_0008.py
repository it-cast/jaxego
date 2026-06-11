"""Migration 0008 is reversible against LIVE MySQL 8 (@pytest.mark.mysql).

Drives the real alembic chain using EXPLICIT revisions (robust to future migrations):
`upgrade 0008_proofs_tracking_notif` → `downgrade 0007_dispatch_favorites_blocks` →
`upgrade 0008_proofs_tracking_notif`, and asserts the five Phase-9 tables
(delivery_proofs, delivery_locations, notifications, push_subscriptions,
direct_payment_confirmations, payment_disputes) + the `deliveries.cancel_cost_cents`
column appear after upgrade, vanish after downgrade, and come back — proving the
`downgrade` is symmetric and does not trip the FK-backing-index errno 1553 that broke
the 0006 downgrade (lição da 0006).

We pin EXPLICIT revisions instead of `head`/`-1`: once 0009+ exists, `head`=0009 and
`downgrade -1` goes 0009→0008 (not 0008→0007), so the relative test would break even
though 0008 itself is still reversible. Explicit revisions stay correct as migrations
stack up. The helper restores `head` in a `finally` so the rest of the live suite sees a
fully-migrated schema. Skipped in dev via `-m "not mysql"` (the chain has MySQL-only
DDL). Run live:

    cd apps/api && uv run pytest -m mysql tests/db/test_migration_0008.py
"""

from __future__ import annotations

import pytest
from alembic import command
from alembic.config import Config

from tests.db.conftest import (
    alembic_config,
    assert_migration_reversible,
    columns,
    tables,
)

pytestmark = pytest.mark.mysql

_REVISION = "0008_proofs_tracking_notif"
_DOWN_REVISION = "0007_dispatch_favorites_blocks"

_NEW_TABLES = (
    "delivery_proofs",
    "delivery_locations",
    "notifications",
    "push_subscriptions",
    "direct_payment_confirmations",
    "payment_disputes",
)


def _assert_present() -> None:
    current = tables()
    for t in _NEW_TABLES:
        assert t in current, t
    assert "cancel_cost_cents" in columns("deliveries")


def _assert_absent() -> None:
    current = tables()
    for t in _NEW_TABLES:
        assert t not in current, t
    assert "cancel_cost_cents" not in columns("deliveries")


@pytest.fixture
def cfg() -> Config:
    return alembic_config()


def test_0008_upgrade_creates_tables(cfg: Config) -> None:
    try:
        command.upgrade(cfg, _REVISION)
        _assert_present()
    finally:
        command.upgrade(cfg, "head")


def test_0008_downgrade_then_upgrade_is_reversible(cfg: Config) -> None:
    assert_migration_reversible(
        cfg,
        revision=_REVISION,
        down_revision=_DOWN_REVISION,
        assert_present=_assert_present,
        assert_absent=_assert_absent,
    )
