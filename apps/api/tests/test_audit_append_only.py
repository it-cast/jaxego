"""Append-only audit_log trigger — MySQL acceptance test (T-16, REQ-004, LOW-3).

Marked `@pytest.mark.mysql`: it requires a LIVE MySQL 8 with migration 0002
applied (the trigger is MySQL-specific; SQLite uses different syntax and is not
the integrity authority). Run against real MySQL with:

    uv run pytest -m mysql tests/test_audit_append_only.py -x

Skipped by default in dev (`-m "not mysql"`). The orchestrator runs it live.

Asserts: INSERT into audit_log succeeds; UPDATE raises MySQL SIGNAL SQLSTATE
'45000'; DELETE raises the same. This is the ROADMAP acceptance criterion for the
append-only guarantee (RN-012 / TH-10).
"""

from __future__ import annotations

import pytest
from app.db.session import engine
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

pytestmark = pytest.mark.mysql


async def _insert_one() -> int:
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
async def test_insert_is_allowed() -> None:
    new_id = await _insert_one()
    assert new_id > 0


@pytest.mark.asyncio
async def test_update_is_blocked_by_trigger() -> None:
    new_id = await _insert_one()
    with pytest.raises(OperationalError) as exc:
        async with engine.begin() as conn:
            await conn.execute(
                text("UPDATE audit_log SET action = :a WHERE id = :id"),
                {"a": "tampered", "id": new_id},
            )
    # MySQL surfaces SIGNAL SQLSTATE '45000' (error 1644).
    assert "1644" in str(exc.value) or "45000" in str(exc.value) or "append-only" in str(exc.value)


@pytest.mark.asyncio
async def test_delete_is_blocked_by_trigger() -> None:
    new_id = await _insert_one()
    with pytest.raises(OperationalError) as exc:
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM audit_log WHERE id = :id"),
                {"id": new_id},
            )
    assert "1644" in str(exc.value) or "45000" in str(exc.value) or "append-only" in str(exc.value)
