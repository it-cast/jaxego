"""Shared helpers for LIVE-MySQL per-migration reversibility tests (@pytest.mark.mysql).

Per-migration reversibility tests MUST drive the alembic chain with EXPLICIT revision
ids, never relative positions (`head` / `-1`). Relative positions move every time a new
migration is stacked on top: once 0009 exists, `head`=0009 and `downgrade -1` goes
0009→0008 (not 0008→0007), so a test asserting "the 0008 column vanishes" breaks even
though 0008 itself is still perfectly reversible. Explicit revisions pin the test to the
exact up/down boundary it means to exercise, immune to future migrations.

Every test restores the DB to `head` in a `finally`, so a test that lands the schema on
an intermediate revision can't poison the rest of the live `-m mysql` suite (which
assumes a fully-migrated schema).
"""

from __future__ import annotations

from collections.abc import Callable

from alembic import command
from alembic.config import Config
from app.core.config import settings
from sqlalchemy import create_engine, inspect


def sync_url() -> str:
    """The MySQL URL with a sync driver for inspect() (asyncmy/aiomysql → pymysql)."""
    return settings.database_url.replace("+asyncmy", "+pymysql").replace("+aiomysql", "+pymysql")


def alembic_config() -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    return cfg


def tables() -> set[str]:
    engine = create_engine(sync_url())
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def columns(table: str) -> set[str]:
    engine = create_engine(sync_url())
    try:
        return {c["name"] for c in inspect(engine).get_columns(table)}
    finally:
        engine.dispose()


def assert_migration_reversible(
    cfg: Config,
    *,
    revision: str,
    down_revision: str,
    assert_present: Callable[[], None],
    assert_absent: Callable[[], None],
) -> None:
    """Prove `revision` is symmetric using EXPLICIT revisions (robust to future migrations).

    Drives: upgrade→`revision` → assert present → downgrade→`down_revision` → assert absent
    → upgrade→`revision` → assert present. ALWAYS restores `head` in a `finally`, so the
    DB never lands on an intermediate revision that would break the rest of the live suite.
    """
    try:
        command.upgrade(cfg, revision)
        assert_present()

        command.downgrade(cfg, down_revision)
        assert_absent()

        command.upgrade(cfg, revision)
        assert_present()
    finally:
        command.upgrade(cfg, "head")
