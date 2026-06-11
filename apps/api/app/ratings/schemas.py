"""Rating API schemas (REQ-033 / D-03). Pydantic validates 1..5 (TH-06 — bound input)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.ratings.models import RATING_MAX_STARS, RATING_MIN_STARS


class RatingCreateBody(BaseModel):
    """Store rates the courier of a FINALIZADA delivery (1-5 + optional comment)."""

    stars: int = Field(..., ge=RATING_MIN_STARS, le=RATING_MAX_STARS)
    comment: str | None = Field(default=None, max_length=500)


class RatingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    delivery_id: int
    courier_id: int
    stars: int
    comment: str | None
