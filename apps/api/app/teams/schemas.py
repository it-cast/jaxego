"""Team schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TeamCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=160)


class TeamUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=2, max_length=160)


class TeamRead(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: int
    area_id: int
    name: str
    deleted_at: datetime | None = None
    created_at: datetime
