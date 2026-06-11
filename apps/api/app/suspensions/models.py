"""SuspensionAppeal + AreaRevenueShare models (REQ-045 / REQ-047 / D-04..D-07).

`SuspensionAppeal` is AREA-SCOPED: it records the suspension's appeal WINDOW for a
subject (a courier or a merchant — `subject_type`/`subject_id`). The suspension itself
reuses the EXISTING state machines (courier/merchant active↔suspended↔banned); this row
only adds the SLA window + decision. The actual `suspended`/`active` transitions are
written by the courier/merchant services and audited (append-only audit_log). When the
SLA passes with NO decision, the SLA job reverts the subject to active and sets
`reverted_at` (idempotent).

`AreaRevenueShare` is AREA-SCOPED parametrised config (REQ-047 / D-07): the share % is
SEED-editable data with an `effective_from` version (ADR-103 style). NO money moves here
— the financial consequence is Phase 15 (DEC-004). The % itself is the owner's decision
(OQ-1); a placeholder `[ASSUMIDO]` value is seeded until decided (see TD-13-01).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin

# Who can be suspended (D-04). Both reuse an existing state machine.
SUBJECT_TYPES = ("courier", "merchant")

# Appeal decision outcomes (D-05). null = undecided (the SLA job may revert it).
APPEAL_DECISIONS = ("upheld", "overturned")


class SuspensionAppeal(Base, AreaScopedMixin, TimestampMixin):
    """A suspension's appeal window with its SLA + decision (REQ-045 / D-05)."""

    __tablename__ = "suspension_appeals"
    __table_args__ = (
        # Find a subject's appeals (open/decided) — no scan.
        Index("ix_suspension_appeals_subject", "subject_type", "subject_id"),
        # The SLA sweep: undecided appeals past due (decision IS NULL, sla_due_at < now).
        Index("ix_suspension_appeals_decision_sla", "decision", "sla_due_at"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    subject_type: Mapped[str] = mapped_column(String(16), nullable=False)
    subject_id: Mapped[int] = mapped_column(BIG_ID, nullable=False)
    # Mandatory suspension reason (D-04 — never silent). Also recorded in audit_log.
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    # The SLA deadline; the job reverts the subject if this passes undecided.
    sla_due_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    # null until decided; upheld (suspension stays) | overturned (lift it).
    decision: Mapped[str | None] = mapped_column(String(16), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    decided_by: Mapped[int | None] = mapped_column(BIG_ID, nullable=True)
    # Set by the SLA job when it auto-reverts (idempotent marker — D-05).
    reverted_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)


class AreaRevenueShare(Base, AreaScopedMixin, TimestampMixin):
    """Parametrised revenue-share config per area (REQ-047 / D-07). NO money moves."""

    __tablename__ = "area_revenue_share"
    __table_args__ = (
        # One row per (area, effective_from) — versioned config (ADR-103 style).
        UniqueConstraint(
            "area_id", "effective_from", name="uq_area_revenue_share_area_effective"
        ),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    # The share percentage (e.g. 10.00 = 10%). Numeric, never Float. [ASSUMIDO] seed.
    share_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    created_by: Mapped[int | None] = mapped_column(BIG_ID, nullable=True)
