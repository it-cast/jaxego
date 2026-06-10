"""Ranking key for the automatic cascade tier (D-02 / ADR-013). Pure + testable.

The ranking orders eligible NON-favorite couriers. The sort key is a tuple
(smaller is better): ETA first (closest by road), then current load (least busy),
then price (cheapest). `score` is in the signature so v1.1 can wire its weight at
the SAME call-site without a change — but in M1 it has weight ZERO (ADR-013: score
is collected and exhibited, never financially weighted yet).
"""

from __future__ import annotations

# ADR-013 — M1 score weight is ZERO (no consequence in the ordering).
_SCORE_WEIGHT_M1 = 0.0


def rank_key(*, eta_s: int, load: int, price_cents: int, score: float) -> tuple:
    """Sort key (smaller is better): (eta, load, price, -score*0) — M1 (ADR-013).

    Orders by ETA (closest first), then load (least busy), then price (cheapest).
    `score` is multiplied by a ZERO weight in M1, so it does NOT change the order;
    the term is kept so v1.1 can flip the weight without touching call-sites.
    """
    return (eta_s, load, price_cents, -score * _SCORE_WEIGHT_M1)
