"""Migration 0011 reversibility — MySQL acceptance test (T-01).

Marked `@pytest.mark.mysql`: requires a LIVE MySQL 8. Asserts that upgrade →
downgrade → upgrade round-trips cleanly (FK order in `downgrade` is correct — no
errno 1553/1217). Skipped by default in dev (`-m "not mysql"`); the orchestrator
runs it against real MySQL.

    uv run pytest -m mysql tests/scores/test_migration_0011.py -x
"""

from __future__ import annotations

import pytest
from alembic import command
from alembic.config import Config

pytestmark = pytest.mark.mysql

_GOV_TABLES = (
    "score_weights",
    "courier_score_snapshots",
    "courier_ratings",
    "suspension_appeals",
    "area_revenue_share",
)


def _alembic_cfg() -> Config:
    """Alembic config pointed at the configured DATABASE_URL."""
    from app.core.config import settings

    cfg = Config("alembic.ini")
    # Alembic uses a sync driver; strip the async driver suffix if present.
    url = settings.database_url.replace("+aiomysql", "+pymysql").replace("+asyncmy", "+pymysql")
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


@pytest.mark.mysql
def test_migration_0011_round_trips() -> None:
    """upgrade head → downgrade -1 → upgrade head leaves the gov tables present."""
    import sqlalchemy as sa

    cfg = _alembic_cfg()

    command.upgrade(cfg, "head")
    command.downgrade(cfg, "0010_public_api_webhooks")

    from app.core.config import settings

    url = settings.database_url.replace("+aiomysql", "+pymysql").replace("+asyncmy", "+pymysql")
    engine = sa.create_engine(url)
    insp = sa.inspect(engine)
    tables_after_down = set(insp.get_table_names())
    # After downgrade, none of the Phase 13 tables should remain.
    for t in _GOV_TABLES:
        assert t not in tables_after_down, f"{t} survived downgrade"

    command.upgrade(cfg, "head")
    insp = sa.inspect(engine)
    tables_after_up = set(insp.get_table_names())
    for t in _GOV_TABLES:
        assert t in tables_after_up, f"{t} missing after re-upgrade"
    engine.dispose()
