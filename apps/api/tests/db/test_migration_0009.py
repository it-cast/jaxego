"""Migration 0009 is reversible against LIVE MySQL 8 (@pytest.mark.mysql).

Drives the real alembic chain using EXPLICIT revisions (robust to future migrations):
`upgrade 0009_safe2pay_billing_escrow` → `downgrade 0008_proofs_tracking_notif` →
`upgrade 0009_safe2pay_billing_escrow`, and asserts the three Phase-10 tables
(platform_charges, escrow_ledger, payment_webhook_events) + the
`merchant_subscriptions.billing_status`/`safe2pay_token` and `couriers.s2p_recipient_id`
columns appear after upgrade, vanish after downgrade, and come back — proving the
`downgrade` is symmetric and does not trip errno 1553 (lição 0006/0008). The revision id
is 28 chars (≤ 32 — alembic_version VARCHAR(32) lição).

We pin EXPLICIT revisions instead of `head`/`-1` so this test stays correct when 0010+
is stacked on top (with relative `-1` it would silently drift to the 0010→0009 boundary
and break). The helper restores `head` in a `finally` so the rest of the live suite sees
a fully-migrated schema. Skipped in dev via `-m "not mysql"`. Run live:

    cd apps/api && uv run pytest -m mysql tests/db/test_migration_0009.py
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

_REVISION = "0009_safe2pay_billing_escrow"
_DOWN_REVISION = "0008_proofs_tracking_notif"

_NEW_TABLES = (
    "platform_charges",
    "escrow_ledger",
    "payment_webhook_events",
)


def _assert_present() -> None:
    current = tables()
    for t in _NEW_TABLES:
        assert t in current, t
    assert "billing_status" in columns("merchant_subscriptions")
    assert "safe2pay_token" in columns("merchant_subscriptions")
    assert "s2p_recipient_id" in columns("couriers")


def _assert_absent() -> None:
    current = tables()
    for t in _NEW_TABLES:
        assert t not in current, t
    assert "billing_status" not in columns("merchant_subscriptions")
    assert "s2p_recipient_id" not in columns("couriers")


@pytest.fixture
def cfg() -> Config:
    return alembic_config()


def test_0009_upgrade_creates_tables_and_columns(cfg: Config) -> None:
    try:
        command.upgrade(cfg, _REVISION)
        _assert_present()
    finally:
        command.upgrade(cfg, "head")


def test_0009_downgrade_then_upgrade_is_reversible(cfg: Config) -> None:
    assert_migration_reversible(
        cfg,
        revision=_REVISION,
        down_revision=_DOWN_REVISION,
        assert_present=_assert_present,
        assert_absent=_assert_absent,
    )
