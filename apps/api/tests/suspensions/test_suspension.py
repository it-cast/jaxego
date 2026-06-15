"""Suspension/appeal service: audited, reason required, overturned lifts (T-05 / REQ-045)."""

from __future__ import annotations

import pytest
from app.audit.models import AuditLog
from app.couriers.models import Courier
from app.suspensions.service import (
    ReasonRequiredError,
    decide_appeal,
    open_suspension,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.suspensions.conftest import SuspensionWorld


async def _audit_actions(session: AsyncSession) -> list[str]:
    return [r[0] for r in (await session.execute(select(AuditLog.action))).all()]


@pytest.mark.asyncio
async def test_open_suspension_requires_reason(
    db_session: AsyncSession, suspension_world: SuspensionWorld
) -> None:
    with pytest.raises(ReasonRequiredError):
        await open_suspension(
            db_session,
            subject_type="courier",
            subject_id=suspension_world.courier_id,
            area_id=suspension_world.area_id,
            reason="   ",
            actor_id=suspension_world.admin_id,
        )


@pytest.mark.asyncio
async def test_open_suspension_transitions_and_audits(
    db_session: AsyncSession, suspension_world: SuspensionWorld
) -> None:
    appeal = await open_suspension(
        db_session,
        subject_type="courier",
        subject_id=suspension_world.courier_id,
        area_id=suspension_world.area_id,
        reason="comportamento abusivo",
        actor_id=suspension_world.admin_id,
    )
    courier = await db_session.get(Courier, suspension_world.courier_id)
    assert courier.status == "suspended"
    assert appeal.decision is None
    assert appeal.sla_due_at > appeal.opened_at
    # The suspension is audited (before/after + reason).
    assert "courier.suspended" in await _audit_actions(db_session)


@pytest.mark.asyncio
async def test_overturned_appeal_lifts_suspension(
    db_session: AsyncSession, suspension_world: SuspensionWorld
) -> None:
    appeal = await open_suspension(
        db_session,
        subject_type="courier",
        subject_id=suspension_world.courier_id,
        area_id=suspension_world.area_id,
        reason="engano",
        actor_id=suspension_world.admin_id,
    )
    await decide_appeal(
        db_session,
        appeal_id=appeal.id,
        area_id=suspension_world.area_id,
        decision="overturned",
        actor_id=suspension_world.admin_id,
    )
    courier = await db_session.get(Courier, suspension_world.courier_id)
    assert courier.status == "active"
    assert "courier.appeal_overturned" in await _audit_actions(db_session)


@pytest.mark.asyncio
async def test_upheld_appeal_keeps_suspension(
    db_session: AsyncSession, suspension_world: SuspensionWorld
) -> None:
    appeal = await open_suspension(
        db_session,
        subject_type="courier",
        subject_id=suspension_world.courier_id,
        area_id=suspension_world.area_id,
        reason="grave",
        actor_id=suspension_world.admin_id,
    )
    await decide_appeal(
        db_session,
        appeal_id=appeal.id,
        area_id=suspension_world.area_id,
        decision="upheld",
        actor_id=suspension_world.admin_id,
    )
    courier = await db_session.get(Courier, suspension_world.courier_id)
    assert courier.status == "suspended"
    assert "courier.appeal_upheld" in await _audit_actions(db_session)
