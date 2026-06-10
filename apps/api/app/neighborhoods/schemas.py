"""Neighborhood API contracts (Pydantic v2, extra='forbid' — A03)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NeighborhoodCreate(BaseModel):
    """Create a neighborhood. Polygon is OPTIONAL (name-only is valid — M1)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    is_informal: bool = False
    # GeoJSON Polygon (optional). Validated server-side (shapely) before the DB.
    polygon_geojson: dict | None = None


class NeighborhoodPolygonUpdate(BaseModel):
    """Set/replace a neighborhood's polygon (GeoJSON Polygon)."""

    model_config = ConfigDict(extra="forbid")

    polygon_geojson: dict


class NeighborhoodRead(BaseModel):
    """Neighborhood projection returned by the API."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    area_id: int
    name: str
    is_informal: bool
    # Derived: 'defined' when a polygon exists, else 'by_name'.
    polygon_status: Literal["defined", "by_name"]
