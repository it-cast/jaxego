"""Score models (REQ-020 / ADR-013 / D-01/D-02).

`ScoreWeight` is a GLOBAL seed (like `subscription_plans`): the per-component weights
are parametrised SEED data (DRV-009), never hardcoded in a serving path. It is NOT
area-scoped — weights are a platform-wide catalog.

`CourierScoreSnapshot` is AREA-SCOPED: one row per (courier, day). `components` JSON
carries the explainable breakdown (name / raw value / weight / contribution) so the
admin sees WHY the score is what it is (transparency is the requirement — ADR-013, not
an ornament). `level` is one of the 5 tokens (probation/bronze/prata/ouro/diamante).

The snapshot is DERIVED from auditable signals (no direct-write endpoint — TH-05). It
NEVER feeds the dispatch ranking in M1 (ADR-013 — isolation verified in scores/test).
"""

from __future__ import annotations

from datetime import date as date_type
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, AreaScopedMixin, TimestampMixin

# The 5 level tokens (D-01) mapped to color.score_level.* in tokens.json.
SCORE_LEVELS = ("probation", "bronze", "prata", "ouro", "diamante")

# The score components (D-01). Weights live in the SEED (DRV-009), never hardcoded.
SCORE_COMPONENTS = (
    "acceptance_rate",  # taxa de aceite (dispatch)
    "punctuality",  # pontualidade (proofs)
    "proof_ok",  # comprovação ok (proofs)
    "low_cancellation",  # poucos cancelamentos (deliveries)
    "ratings",  # avaliações das lojas (courier_ratings — novo)
)


class ScoreWeight(Base, TimestampMixin):
    """GLOBAL parametrised weight for one score component (DRV-009 — seed-editable)."""

    __tablename__ = "score_weights"

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    # Natural key for idempotent seed upsert.
    component: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    # Weight in [0,1]; the active set should sum to ~1 (validated at seed time).
    weight: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CourierScoreSnapshot(Base, AreaScopedMixin, TimestampMixin):
    """One explainable daily score snapshot for a courier (REQ-020 / D-01)."""

    __tablename__ = "courier_score_snapshots"
    __table_args__ = (
        # One snapshot per (courier, day) — the idempotent job key (1/dia/courier).
        UniqueConstraint(
            "courier_id", "snapshot_date", name="uq_courier_score_snapshots_courier_date"
        ),
        # The courier's own history / admin breakdown query (no scan).
        Index(
            "ix_courier_score_snapshots_courier_date",
            "courier_id",
            "snapshot_date",
        ),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    courier_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    snapshot_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    # 0..100 derived score (Numeric, never Float).
    total_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    # Explainable breakdown: [{component, raw, weight, contribution}, ...].
    components: Mapped[list] = mapped_column(JSON, nullable=False)
