"""Suspension / appeal service (REQ-045 / D-04/D-05) + revenue-share config (D-07).

Suspension REUSES the existing state machines (courier/merchant active↔suspended). This
module:
- opens a suspension (subject → suspended) with a MANDATORY reason, always AUDITED
  (before/after + reason + actor) in the append-only audit_log (TH-03);
- opens the appeal window (`suspension_appeals` with `sla_due_at`);
- records the admin decision (upheld | overturned) — overturned lifts the suspension
  (subject → active), also audited;
- exposes `revert_subject` used by the SLA job (T-07) to auto-lift an undecided,
  past-due suspension (subject → active + audit + alert).

The financial consequence of a dispute is NOT here (DEC-004 → Phase 15). `share_pct` is
parametrised config only (no money moves).

All datetimes aware UTC (TD-010). No PII in any audit payload (TH-07 — only ids/states).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit
from app.core.exceptions import AppError
from app.couriers.models import Courier
from app.couriers.state_machine import assert_courier_transition
from app.merchants.models import Merchant
from app.merchants.state_machine import assert_transition as assert_merchant_transition
from app.payments_direct.models import PaymentDispute
from app.suspensions.models import AreaRevenueShare, SuspensionAppeal

logger = structlog.get_logger("suspensions")

# Default appeal SLA window (D-05). [ASSUMIDO] — 72h. Parametrisable later.
DEFAULT_APPEAL_SLA = timedelta(hours=72)

# [ASSUMIDO] revenue share % (OQ-1 — owner's decision; see TD-13-01). Seed-editable.
ASSUMED_REVENUE_SHARE_PCT = Decimal("10.00")

SubjectType = Literal["courier", "merchant"]
Decision = Literal["upheld", "overturned"]


class SubjectNotFoundError(AppError):
    status_code = 404
    code = "subject_not_found"

    def __init__(self) -> None:
        super().__init__("Sujeito não encontrado.")


class ReasonRequiredError(AppError):
    """A suspension without a reason is blocked (D-04 — never silent)."""

    status_code = 422
    code = "reason_required"

    def __init__(self) -> None:
        super().__init__("Informe o motivo da suspensão.")


class AppealNotFoundError(AppError):
    status_code = 404
    code = "appeal_not_found"

    def __init__(self) -> None:
        super().__init__("Recurso não encontrado.")


class AppealAlreadyDecidedError(AppError):
    status_code = 409
    code = "appeal_already_decided"

    def __init__(self) -> None:
        super().__init__("Este recurso já foi decidido.")


async def _load_subject(
    session: AsyncSession, *, subject_type: SubjectType, subject_id: int, area_id: int | None
) -> Courier | Merchant:
    """Load a courier/merchant with area in the WHERE clause (TH-03 → 404 outside scope)."""
    model = Courier if subject_type == "courier" else Merchant
    stmt = select(model).where(model.id == subject_id)
    if area_id is not None:
        stmt = stmt.where(model.area_id == area_id)
    subject = (await session.execute(stmt)).scalar_one_or_none()
    if subject is None:
        raise SubjectNotFoundError()
    return subject


def _assert_to(subject_type: SubjectType, current: str, target: str) -> None:
    if subject_type == "courier":
        assert_courier_transition(current, target)
    else:
        assert_merchant_transition(current, target)


async def open_suspension(
    session: AsyncSession,
    *,
    subject_type: SubjectType,
    subject_id: int,
    area_id: int,
    reason: str,
    actor_id: int,
    sla: timedelta = DEFAULT_APPEAL_SLA,
    cross_area_bypass: bool = False,
) -> SuspensionAppeal:
    """Suspend a subject (audited) and open its appeal window with an SLA (D-04/D-05)."""
    if not reason or not reason.strip():
        raise ReasonRequiredError()

    subject = await _load_subject(
        session, subject_type=subject_type, subject_id=subject_id, area_id=area_id
    )
    before = subject.status
    _assert_to(subject_type, before, "suspended")
    subject.status = "suspended"

    await write_audit(
        session,
        actor_id=actor_id,
        action=f"{subject_type}.suspended",
        area_id=area_id,
        before={"status": before},
        after={"status": "suspended", "reason": reason},
        cross_area_bypass=cross_area_bypass,
    )

    now = datetime.now(UTC)
    appeal = SuspensionAppeal(
        area_id=area_id,
        subject_type=subject_type,
        subject_id=subject_id,
        reason=reason,
        opened_at=now,
        sla_due_at=now + sla,
    )
    session.add(appeal)
    await session.flush()
    return appeal


async def list_appeals(
    session: AsyncSession,
    *,
    area_id: int | None,
    open_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[SuspensionAppeal]:
    """List suspension appeals within scope (area in the WHERE clause when scoped)."""
    stmt = (
        select(SuspensionAppeal)
        .order_by(SuspensionAppeal.opened_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if area_id is not None:
        stmt = stmt.where(SuspensionAppeal.area_id == area_id)
    if open_only:
        stmt = stmt.where(SuspensionAppeal.decision.is_(None))
    return list((await session.execute(stmt)).scalars().all())


async def decide_appeal(
    session: AsyncSession,
    *,
    appeal_id: int,
    area_id: int | None,
    decision: Decision,
    actor_id: int,
    cross_area_bypass: bool = False,
) -> SuspensionAppeal:
    """Record an appeal decision; `overturned` lifts the suspension (audited)."""
    stmt = select(SuspensionAppeal).where(SuspensionAppeal.id == appeal_id)
    if area_id is not None:
        stmt = stmt.where(SuspensionAppeal.area_id == area_id)
    appeal = (await session.execute(stmt)).scalar_one_or_none()
    if appeal is None:
        raise AppealNotFoundError()
    if appeal.decision is not None:
        raise AppealAlreadyDecidedError()

    appeal.decision = decision
    appeal.decided_at = datetime.now(UTC)
    appeal.decided_by = actor_id

    if decision == "overturned":
        await _revert(
            session,
            appeal=appeal,
            actor_id=actor_id,
            action_suffix="appeal_overturned",
            cross_area_bypass=cross_area_bypass,
        )
    else:
        await write_audit(
            session,
            actor_id=actor_id,
            action=f"{appeal.subject_type}.appeal_upheld",
            area_id=appeal.area_id,
            after={"appeal_id": appeal.id, "decision": "upheld"},
            cross_area_bypass=cross_area_bypass,
        )
    await session.flush()
    return appeal


async def _revert(
    session: AsyncSession,
    *,
    appeal: SuspensionAppeal,
    actor_id: int | None,
    action_suffix: str,
    cross_area_bypass: bool = False,
) -> None:
    """Transition the appeal's subject back to active (audited). Idempotent-safe."""
    subject = await _load_subject(
        session,
        subject_type=appeal.subject_type,  # type: ignore[arg-type]
        subject_id=appeal.subject_id,
        area_id=None,
    )
    before = subject.status
    if before != "suspended":
        return  # already lifted (idempotent) — nothing to do
    _assert_to(appeal.subject_type, before, "active")  # type: ignore[arg-type]
    subject.status = "active"
    await write_audit(
        session,
        actor_id=actor_id,
        action=f"{appeal.subject_type}.{action_suffix}",
        area_id=appeal.area_id,
        before={"status": before},
        after={"status": "active", "appeal_id": appeal.id},
        cross_area_bypass=cross_area_bypass,
    )


# ---------------------------------------------------------------------------
# Disputes (REQ-044 / D-08) — administrative decision ONLY, NO financial effect.
# ---------------------------------------------------------------------------
class DisputeNotFoundError(AppError):
    status_code = 404
    code = "dispute_not_found"

    def __init__(self) -> None:
        super().__init__("Disputa não encontrada.")


async def list_disputes(
    session: AsyncSession, *, area_id: int | None, limit: int = 50, offset: int = 0
) -> list[PaymentDispute]:
    """List payment disputes (Phase 9 primitive) within scope (cursor-friendly)."""
    stmt = (
        select(PaymentDispute).order_by(PaymentDispute.opened_at.desc()).limit(limit).offset(offset)
    )
    if area_id is not None:
        stmt = stmt.where(PaymentDispute.area_id == area_id)
    return list((await session.execute(stmt)).scalars().all())


async def record_dispute_decision(
    session: AsyncSession,
    *,
    dispute_id: int,
    area_id: int | None,
    outcome: Literal["procedente", "improcedente"],
    actor_id: int,
    note: str | None = None,
    cross_area_bypass: bool = False,
) -> PaymentDispute:
    """Register an ADMINISTRATIVE dispute decision (audited). NO financial effect.

    DEC-004 / Phase 15: the financial consequence (90-day block, restitution) is
    DEFERRED. This only marks the dispute `resolved` and audits the decision — it does
    NOT move money or block any account. The financial resolution is wired in Phase 15
    at THIS call-site (placeholder below).
    """
    stmt = select(PaymentDispute).where(PaymentDispute.id == dispute_id)
    if area_id is not None:
        stmt = stmt.where(PaymentDispute.area_id == area_id)
    dispute = (await session.execute(stmt)).scalar_one_or_none()
    if dispute is None:
        raise DisputeNotFoundError()

    before = dispute.status
    dispute.status = "resolved"
    await write_audit(
        session,
        actor_id=actor_id,
        action="dispute.decision_recorded",
        area_id=dispute.area_id,
        before={"status": before},
        after={"dispute_id": dispute.id, "outcome": outcome, "note": note},
        cross_area_bypass=cross_area_bypass,
    )
    # --- Phase 15 placeholder (DEC-004) ---------------------------------------
    # The financial consequence of a `procedente` dispute (2 procedentes/30d → 90-day
    # block, restitution, score→fatura) is INTENTIONALLY NOT implemented here. Wire it
    # at this call-site in Phase 15. Do not add money/block logic in M1.
    # --------------------------------------------------------------------------
    await session.flush()
    return dispute


# ---------------------------------------------------------------------------
# Revenue share config (REQ-047 / D-07) — parametrised, NO money moves.
# ---------------------------------------------------------------------------
async def seed_revenue_share_if_missing(session: AsyncSession, *, area_id: int) -> None:
    """Seed the [ASSUMIDO] revenue-share % for an area if none exists (idempotent)."""
    existing = (
        await session.execute(
            select(AreaRevenueShare.id).where(AreaRevenueShare.area_id == area_id)
        )
    ).first()
    if existing is None:
        session.add(
            AreaRevenueShare(
                area_id=area_id,
                share_pct=ASSUMED_REVENUE_SHARE_PCT,
                effective_from=datetime.now(UTC),
            )
        )
        await session.flush()


async def current_revenue_share(session: AsyncSession, *, area_id: int) -> AreaRevenueShare | None:
    """The latest effective revenue-share config for an area (no money — config only)."""
    stmt = (
        select(AreaRevenueShare)
        .where(AreaRevenueShare.area_id == area_id)
        .order_by(AreaRevenueShare.effective_from.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def set_revenue_share(
    session: AsyncSession,
    *,
    area_id: int,
    share_pct: Decimal,
    actor_id: int,
) -> AreaRevenueShare:
    """Add a new effective revenue-share config version (audited). NO money moves."""
    now = datetime.now(UTC)
    row = AreaRevenueShare(
        area_id=area_id,
        share_pct=share_pct,
        effective_from=now,
        created_by=actor_id,
    )
    session.add(row)
    await write_audit(
        session,
        actor_id=actor_id,
        action="area.revenue_share_set",
        area_id=area_id,
        after={"share_pct": str(share_pct), "effective_from": now.isoformat()},
        cross_area_bypass=True,  # set by the platform admin (cross-area surface)
    )
    await session.flush()
    return row
