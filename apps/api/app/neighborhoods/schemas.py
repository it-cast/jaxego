"""Neighborhood API contracts (Pydantic v2, extra='forbid' — A03)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class NeighborhoodCreate(BaseModel):
    """Create a neighborhood by name (polygon support removed)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    is_informal: bool = False


class NeighborhoodRead(BaseModel):
    """Neighborhood projection returned by the API."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    area_id: int
    name: str
    is_informal: bool
