"""Area API contracts (Pydantic v2, extra='forbid' — A03)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AreaCreate(BaseModel):
    """Create an area (platform admin only)."""

    model_config = ConfigDict(extra="forbid")

    codename: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=160)
    config: dict = Field(default_factory=dict)


class AreaUpdate(BaseModel):
    """Patch an area's mutable fields (platform admin only)."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=160)
    config: dict | None = None


class AreaRead(BaseModel):
    """Area projection returned by the API."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    codename: str
    name: str
    config: dict
    deleted_at: datetime | None
    created_at: datetime
