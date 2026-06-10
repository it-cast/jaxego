"""Append-only audit_log trigger — MySQL acceptance test (T-16, REQ-004, LOW-3).

Marked `@pytest.mark.mysql`: it requires a LIVE MySQL 8 with migration 0002
applied (the trigger is MySQL-specific; SQLite uses different syntax and is not
the integrity authority). Run against real MySQL with:

    uv run pytest -m mysql tests/test_audit_append_only.py -x

Skipped by default in dev (`-m "not mysql"`). The orchestrator runs it live.

Asserts: INSERT into audit_log succeeds; UPDATE raises MySQL SIGNAL SQLSTATE
'45000'; DELETE raises the same. This is the ROADMAP acceptance criterion for the
append-only guarantee (RN-012 / TH-10).

Connection lifecycle: these tests use a DEDICATED async engine built and disposed
inside the test's own event loop (the `mysql_engine` fixture), instead of the
process-wide `app.db.session.engine`. The shared engine is created at import time
(outside any test loop) and pools aiomysql connections; when a function-scoped
test loop closes, the pooled `aiomysql.Connection.__del__` later fires against an
already-closed loop and raises `RuntimeError: Event loop is closed`, which pytest's
`unraisableexception` plugin escalates into a spurious FAILED. Disposing a per-test
engine within the same loop (`await engine.dispose()` in teardown) closes every
connection before the loop tears down, so no `__del__` ever runs on a dead loop.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from app.core.config import settings
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

pytestmark = pytest.mark.mysql


@pytest_asyncio.fixture
async def mysql_engine() -> AsyncIterator[AsyncEngine]:
    """A dedicated async engine created and disposed within the test event loop.

    NullPool keeps no connection alive between checkouts, and the explicit
    `await engine.dispose()` in teardown closes everything inside this loop, so no
    aiomysql connection is ever finalized against a closed loop on Windows.
    """
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(
        settings.database_url,
        echo=False,
        poolclass=NullPool,
    )
    try:
        yield engine
    finally:
        await engine.dispose()


async def _insert_one(engine: AsyncEngine) -> int:
    """Insert one audit_log row and return its id."""
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "INSERT INTO audit_log (action, cross_area_bypass, created_at) "
                "VALUES (:action, :bypass, UTC_TIMESTAMP(6))"
            ),
            {"action": "test.insert", "bypass": False},
        )
        # lastrowid is available on the cursor result.
        return int(result.lastrowid)  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_insert_is_allowed(mysql_engine: AsyncEngine) -> None:
    new_id = await _insert_one(mysql_engine)
    assert new_id > 0


@pytest.mark.asyncio
async def test_update_is_blocked_by_trigger(mysql_engine: AsyncEngine) -> None:
    new_id = await _insert_one(mysql_engine)
    with pytest.raises(OperationalError) as exc:
        async with mysql_engine.begin() as conn:
            await conn.execute(
                text("UPDATE audit_log SET action = :a WHERE id = :id"),
                {"a": "tampered", "id": new_id},
            )
    # MySQL surfaces SIGNAL SQLSTATE '45000' (error 1644).
    assert "1644" in str(exc.value) or "45000" in str(exc.value) or "append-only" in str(exc.value)


@pytest.mark.asyncio
async def test_delete_is_blocked_by_trigger(mysql_engine: AsyncEngine) -> None:
    new_id = await _insert_one(mysql_engine)
    with pytest.raises(OperationalError) as exc:
        async with mysql_engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM audit_log WHERE id = :id"),
                {"id": new_id},
            )
    assert "1644" in str(exc.value) or "45000" in str(exc.value) or "append-only" in str(exc.value)
