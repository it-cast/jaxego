"""Migration 0010 is reversible against LIVE MySQL 8 (@pytest.mark.mysql).

Drives the real alembic chain with EXPLICIT revisions (robust to future migrations):
`upgrade 0010_public_api_webhooks` → `downgrade 0009_safe2pay_billing_escrow` →
`upgrade 0010_public_api_webhooks`, asserting the four Phase-12 tables (api_keys,
api_idempotency_keys, webhook_endpoints, webhook_deliveries) + the
`merchants.external_ref` column appear after upgrade, vanish after downgrade, and
come back — proving the `downgrade` is symmetric and does not trip errno 1553
(children-first drop, lição 0006/0008/0009). The revision id is 24 chars (≤ 32 —
alembic_version VARCHAR(32) lição).

Skipped in dev via `-m "not mysql"`. Run live:

    cd apps/api && uv run pytest -m mysql tests/db/test_migration_0010.py
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

_REVISION = "0010_public_api_webhooks"
_DOWN_REVISION = "0009_safe2pay_billing_escrow"

_NEW_TABLES = (
    "api_keys",
    "api_idempotency_keys",
    "webhook_endpoints",
    "webhook_deliveries",
)


def _assert_present() -> None:
    current = tables()
    for t in _NEW_TABLES:
        assert t in current, t
    assert "external_ref" in columns("merchants")


def _assert_absent() -> None:
    current = tables()
    for t in _NEW_TABLES:
        assert t not in current, t
    assert "external_ref" not in columns("merchants")


@pytest.fixture
def cfg() -> Config:
    return alembic_config()


def test_0010_upgrade_creates_tables_and_columns(cfg: Config) -> None:
    try:
        command.upgrade(cfg, _REVISION)
        _assert_present()
    finally:
        command.upgrade(cfg, "head")


def test_0010_downgrade_then_upgrade_is_reversible(cfg: Config) -> None:
    assert_migration_reversible(
        cfg,
        revision=_REVISION,
        down_revision=_DOWN_REVISION,
        assert_present=_assert_present,
        assert_absent=_assert_absent,
    )
