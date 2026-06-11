"""Score composition + level mapping + idempotent daily snapshot (REQ-020 / ADR-013).

Composition is parametrised: each component's RAW value (0..1) is multiplied by its
SEED weight (`score_weights`, DRV-009) and summed, then scaled to 0..100. Weights are
NEVER hardcoded in a serving path — they come from the DB seed. The mapping to a level
(probation/bronze/prata/ouro/diamante) uses fixed thresholds (a presentation band, not
money — ADR-013).

`build_snapshot` is idempotent per (courier, day): it UPSERTs the row for today, so the
daily job may run more than once without creating duplicates (the UNIQUE
(courier_id, snapshot_date) is the structural guard; the service updates in place).

ZERO financial/operational effect (ADR-013): nothing here is read by dispatch/ranking;
the isolation is proven by `tests/scores/test_isolation_ranking.py` (T-04).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.scores.models import (
    SCORE_COMPONENTS,
    CourierScoreSnapshot,
    ScoreWeight,
)

# [ASSUMIDO] seed weights (DRV-009) — editable seed data, NEVER hardcoded in a serving
# path. They are inserted into `score_weights` and read back from the DB. The active set
# sums to 1.0 (validated below).
SCORE_WEIGHT_SEEDS: tuple[dict[str, object], ...] = (
    {"component": "acceptance_rate", "weight": Decimal("0.25"), "sort_order": 0},
    {"component": "punctuality", "weight": Decimal("0.25"), "sort_order": 1},
    {"component": "proof_ok", "weight": Decimal("0.20"), "sort_order": 2},
    {"component": "low_cancellation", "weight": Decimal("0.15"), "sort_order": 3},
    {"component": "ratings", "weight": Decimal("0.15"), "sort_order": 4},
)

# Level thresholds (D-01) — total_score in 0..100. Presentation band only (ADR-013).
# [(min_inclusive, level)] checked high→low.
_LEVEL_BANDS: tuple[tuple[float, str], ...] = (
    (90.0, "diamante"),
    (75.0, "ouro"),
    (55.0, "prata"),
    (35.0, "bronze"),
    (0.0, "probation"),
)


@dataclass(frozen=True)
class CourierSignals:
    """Raw 0..1 signals for one courier (derived from existing data)."""

    acceptance_rate: float = 0.0
    punctuality: float = 0.0
    proof_ok: float = 0.0
    low_cancellation: float = 0.0
    ratings: float = 0.0


def level_for(total_score: float) -> str:
    """Map a 0..100 score to a level token (probation..diamante)."""
    for threshold, level in _LEVEL_BANDS:
        if total_score >= threshold:
            return level
    return "probation"


async def seed_weights_if_missing(session: AsyncSession) -> None:
    """Idempotent upsert of the parametrised score weights by `component` (DRV-009)."""
    for seed in SCORE_WEIGHT_SEEDS:
        existing = (
            await session.execute(
                select(ScoreWeight).where(ScoreWeight.component == str(seed["component"]))
            )
        ).scalar_one_or_none()
        if existing is None:
            session.add(ScoreWeight(**seed))  # type: ignore[arg-type]
        else:
            existing.weight = Decimal(str(seed["weight"]))
            existing.sort_order = int(seed["sort_order"])  # type: ignore[arg-type]
            existing.is_active = True
    await session.flush()


async def _active_weights(session: AsyncSession) -> dict[str, float]:
    """Load the active component weights from the SEED (DRV-009 — never hardcoded)."""
    rows = (
        (await session.execute(select(ScoreWeight).where(ScoreWeight.is_active.is_(True))))
        .scalars()
        .all()
    )
    return {r.component: float(r.weight) for r in rows}


def compose(signals: CourierSignals, weights: dict[str, float]) -> tuple[float, list[dict]]:
    """Compose the 0..100 score + explainable breakdown from raw signals × weights.

    Each component contributes `raw * weight * 100`. The breakdown lists every
    component (even a zero one) so the admin sees the full picture (ADR-013).
    """
    raw_by_component = {
        "acceptance_rate": signals.acceptance_rate,
        "punctuality": signals.punctuality,
        "proof_ok": signals.proof_ok,
        "low_cancellation": signals.low_cancellation,
        "ratings": signals.ratings,
    }
    components: list[dict] = []
    total = 0.0
    for name in SCORE_COMPONENTS:
        raw = max(0.0, min(1.0, raw_by_component.get(name, 0.0)))
        weight = weights.get(name, 0.0)
        contribution = round(raw * weight * 100.0, 2)
        total += contribution
        components.append(
            {
                "component": name,
                "raw": round(raw, 4),
                "weight": round(weight, 4),
                "contribution": contribution,
            }
        )
    return round(total, 2), components


async def build_snapshot(
    session: AsyncSession,
    *,
    courier_id: int,
    area_id: int,
    signals: CourierSignals,
    snapshot_date: date | None = None,
) -> CourierScoreSnapshot:
    """Build/refresh today's snapshot for a courier (idempotent per (courier, day)).

    Re-running the daily job updates the SAME row instead of inserting a duplicate
    (UNIQUE (courier_id, snapshot_date) is the structural guard).
    """
    day = snapshot_date or datetime.now(UTC).date()
    weights = await _active_weights(session)
    total, components = compose(signals, weights)
    level = level_for(total)

    existing = (
        await session.execute(
            select(CourierScoreSnapshot).where(
                CourierScoreSnapshot.courier_id == courier_id,
                CourierScoreSnapshot.snapshot_date == day,
            )
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.total_score = Decimal(str(total))
        existing.level = level
        existing.components = components
        await session.flush()
        return existing

    snapshot = CourierScoreSnapshot(
        area_id=area_id,
        courier_id=courier_id,
        snapshot_date=day,
        total_score=Decimal(str(total)),
        level=level,
        components=components,
    )
    session.add(snapshot)
    await session.flush()
    return snapshot


async def latest_snapshot(
    session: AsyncSession, *, courier_id: int, area_id: int | None = None
) -> CourierScoreSnapshot | None:
    """The most recent snapshot for a courier (area in the WHERE clause when scoped)."""
    stmt = (
        select(CourierScoreSnapshot)
        .where(CourierScoreSnapshot.courier_id == courier_id)
        .order_by(CourierScoreSnapshot.snapshot_date.desc())
        .limit(1)
    )
    if area_id is not None:
        stmt = stmt.where(CourierScoreSnapshot.area_id == area_id)
    return (await session.execute(stmt)).scalar_one_or_none()
