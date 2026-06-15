"""Derive raw 0..1 score signals from EXISTING auditable data (REQ-020 / ADR-013).

The snapshot is DERIVED, never directly written (TH-05). Each signal is normalised to
0..1 from data the platform already records:

- `ratings`: average of `courier_ratings.stars` mapped (1..5 → 0..1). No ratings → 0.5
  (neutral prior, so a brand-new courier is not punished).
- `low_cancellation`: 1 - (cancelled / total) over the courier's deliveries.
- `proof_ok`: fraction of finalised deliveries that reached FINALIZADA.
- `acceptance_rate` / `punctuality`: MED-confidence proxies in M1 (delivery completion
  ratio). These are intentionally simple; richer dispatch-offer signals are a v1.1
  refinement (TD — see EXECUTION-LOG). They never feed money/ranking (ADR-013).

PII is NEVER read into these aggregates (only counts/stars), so nothing here can leak a
CPF/phone into a log (TH-07).
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deliveries.models import Delivery
from app.ratings.models import CourierRating
from app.scores.service import CourierSignals

_TERMINAL_OK = ("FINALIZADA", "ENTREGUE")


async def compute_signals(session: AsyncSession, *, courier_id: int) -> CourierSignals:
    """Compute the raw 0..1 signals for a courier from existing data (single queries)."""
    # Ratings average (1..5 → 0..1). Neutral 0.5 prior when there are no ratings yet.
    avg_stars = (
        await session.execute(
            select(func.avg(CourierRating.stars)).where(CourierRating.courier_id == courier_id)
        )
    ).scalar_one_or_none()
    ratings_signal = ((float(avg_stars) - 1.0) / 4.0) if avg_stars is not None else 0.5

    # Delivery outcome counts (one grouped query, no N+1).
    rows = (
        await session.execute(
            select(Delivery.state, func.count(Delivery.id))
            .where(Delivery.courier_id == courier_id)
            .group_by(Delivery.state)
        )
    ).all()
    counts = {state: int(n) for state, n in rows}
    total = sum(counts.values())

    if total == 0:
        # No history → neutral priors (a new courier starts at probation, not punished).
        return CourierSignals(
            acceptance_rate=0.5,
            punctuality=0.5,
            proof_ok=0.5,
            low_cancellation=1.0,
            ratings=ratings_signal,
        )

    cancelled = counts.get("CANCELADA", 0) + counts.get("RECUSADA_NO_DESTINO", 0)
    completed = sum(counts.get(s, 0) for s in _TERMINAL_OK)
    low_cancellation = 1.0 - (cancelled / total)
    completion = completed / total

    return CourierSignals(
        # M1 proxies (MED confidence — TD for v1.1 richer dispatch signals).
        acceptance_rate=completion,
        punctuality=completion,
        proof_ok=completion,
        low_cancellation=low_cancellation,
        ratings=ratings_signal,
    )
