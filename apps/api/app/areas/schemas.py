"""Area API contracts (Pydantic v2, extra='forbid' — A03)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class AreaAdminAssignBody(BaseModel):
    """Assign (or update the role of) an area admin by e-mail (F3.3)."""

    model_config = ConfigDict(extra="forbid")

    user_email: EmailStr
    role: Literal["owner", "manager", "viewer"] = "manager"


class AreaAdminRead(BaseModel):
    """An area-admin membership projection."""

    model_config = ConfigDict(extra="forbid")

    id: int
    area_id: int
    area_name: str = ""
    user_id: int
    user_email: str
    user_name: str = ""
    role: str


class AreaAdminCreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    area_id: int
    email: EmailStr
    name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=10, max_length=128)
    role: Literal["owner", "manager", "viewer"] = "manager"


class AreaAdminUpdateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["owner", "manager", "viewer"] | None = None
    area_id: int | None = None
