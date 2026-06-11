"""Migration 0012 reversibility — MySQL acceptance test (T-02 / REQ-053).

Marked `@pytest.mark.mysql`: requires a LIVE MySQL 8. Asserts that upgrade →
downgrade → upgrade round-trips cleanly for `ai_usage_log` (the table is created on
upgrade, removed on downgrade, recreated on re-upgrade — no orphaned index, no
errno 1553). Skipped by default in dev (`-m "not mysql"`); the orchestrator runs it
against real MySQL.

    uv run pytest -m mysql tests/ai/test_migration_0012.py -x
"""

from __future__ import annotations

import pytest
from alembic import command
from alembic.config import Config

pytestmark = pytest.mark.mysql

_AI_TABLE = "ai_usage_log"


def _alembic_cfg() -> Config:
    """Alembic config pointed at the configured DATABASE_URL (sync driver)."""
    from app.core.config import settings

    cfg = Config("alembic.ini")
    url = settings.database_url.replace("+aiomysql", "+pymysql").replace("+asyncmy", "+pymysql")
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


@pytest.mark.mysql
def test_migration_0012_round_trips() -> None:
    """upgrade head → downgrade -1 → upgrade head leaves ai_usage_log present."""
    import sqlalchemy as sa

    cfg = _alembic_cfg()

    command.upgrade(cfg, "head")
    command.downgrade(cfg, "0011_governance_score_ratings")

    from app.core.config import settings

    url = settings.database_url.replace("+aiomysql", "+pymysql").replace("+asyncmy", "+pymysql")
    engine = sa.create_engine(url)
    insp = sa.inspect(engine)
    assert _AI_TABLE not in set(insp.get_table_names()), "ai_usage_log survived downgrade"

    command.upgrade(cfg, "head")
    insp = sa.inspect(engine)
    assert _AI_TABLE in set(insp.get_table_names()), "ai_usage_log missing after re-upgrade"
    engine.dispose()
