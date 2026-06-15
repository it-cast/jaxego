"""Appeal SLA enforcement job — clock-controlled reversion (T-07 / LOW-1 / D-05).

Asserts the three behaviours from the LOW-1 acceptance criterion:
- overdue + undecided → subject reverts to active + alert emitted (structlog warning);
- decided in time → NOT reverted;
- idempotent → a second run does not revert again (reverted_at guards it).
"""

from __future__ import annotations

from datetime import timedelta

import pytest
import structlog
from app.couriers.models import Courier
from app.suspensions.models import SuspensionAppeal
from app.suspensions.service import decide_appeal, open_suspension
from app.workers.appeals import enforce_appeal_sla
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.suspensions.conftest import SuspensionWorld


@pytest.mark.asyncio
async def test_overdue_undecided_appeal_is_reverted_with_alert(
    db_session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    suspension_world: SuspensionWorld,
) -> None:
    # Open a suspension whose SLA already lapsed (negative window = overdue clock).
    appeal = await open_suspension(
        db_session,
        subject_type="courier",
        subject_id=suspension_world.courier_id,
        area_id=suspension_world.area_id,
        reason="motivo",
        actor_id=suspension_world.admin_id,
        sla=timedelta(hours=-1),  # controlled clock: sla_due_at in the past
    )
    await db_session.commit()

    # Capture structlog events directly (robust vs. stdout/capsys ordering).
    with structlog.testing.capture_logs() as logs:
        reverted = await enforce_appeal_sla({"session_factory": session_factory})
    assert reverted == 1

    async with session_factory() as s:
        courier = await s.get(Courier, suspension_world.courier_id)
        assert courier.status == "active"  # auto-reverted
        row = await s.get(SuspensionAppeal, appeal.id)
        assert row.reverted_at is not None

    # The alert is emitted (structlog warning event 'sla_auto_reverted').
    events = {entry.get("event") for entry in logs}
    assert "appeals.sla_auto_reverted" in events


@pytest.mark.asyncio
async def test_decided_in_time_is_not_reverted(
    db_session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    suspension_world: SuspensionWorld,
) -> None:
    # SLA in the future; decided upheld before it lapses → must NOT be touched.
    appeal = await open_suspension(
        db_session,
        subject_type="courier",
        subject_id=suspension_world.courier_id,
        area_id=suspension_world.area_id,
        reason="motivo",
        actor_id=suspension_world.admin_id,
        sla=timedelta(hours=72),
    )
    await decide_appeal(
        db_session,
        appeal_id=appeal.id,
        area_id=suspension_world.area_id,
        decision="upheld",
        actor_id=suspension_world.admin_id,
    )
    await db_session.commit()

    reverted = await enforce_appeal_sla({"session_factory": session_factory})
    assert reverted == 0

    async with session_factory() as s:
        courier = await s.get(Courier, suspension_world.courier_id)
        assert courier.status == "suspended"  # untouched


@pytest.mark.asyncio
async def test_sla_job_is_idempotent(
    db_session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    suspension_world: SuspensionWorld,
) -> None:
    await open_suspension(
        db_session,
        subject_type="courier",
        subject_id=suspension_world.courier_id,
        area_id=suspension_world.area_id,
        reason="motivo",
        actor_id=suspension_world.admin_id,
        sla=timedelta(hours=-1),
    )
    await db_session.commit()

    first = await enforce_appeal_sla({"session_factory": session_factory})
    second = await enforce_appeal_sla({"session_factory": session_factory})
    assert first == 1
    assert second == 0  # already reverted — not touched again

    async with session_factory() as s:
        count = len((await s.execute(select(SuspensionAppeal))).scalars().all())
        assert count == 1
