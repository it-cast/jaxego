"""Score API schemas (read-only — TH-05: no direct-write of a note).

There is NO write schema for a score: the snapshot is derived by the job. The courier
sees their own latest snapshot (total + level + breakdown); the admin sees the same
breakdown for any courier in scope. The breakdown is the explainability requirement
(ADR-013) — each component carries its raw value, weight and contribution.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class ScoreComponentRead(BaseModel):
    """One explainable component line: raw value, weight, contribution."""

    component: str
    raw: float
    weight: float
    contribution: float


class CourierScoreRead(BaseModel):
    """A courier's latest score snapshot with its explainable breakdown."""

    model_config = ConfigDict(from_attributes=True)

    courier_id: int
    snapshot_date: date
    total_score: float
    level: str
    components: list[ScoreComponentRead]
