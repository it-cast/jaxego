"""Suspension / appeal / dispute API schemas (REQ-044/045 / D-04/D-05/D-08).

Inputs are bound by Pydantic (TH-06): `subject_type` is a Literal enum, `reason` is
required and length-bounded, `decision` is a Literal. No free SQL is ever built from
these values.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SuspensionCreateBody(BaseModel):
    """Open a suspension for a courier/merchant (reason mandatory — D-04)."""

    subject_type: Literal["courier", "merchant"]
    subject_id: int
    reason: str = Field(..., min_length=3, max_length=500)


class AppealRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_type: str
    subject_id: int
    reason: str
    opened_at: datetime
    sla_due_at: datetime
    decision: str | None
    decided_at: datetime | None
    reverted_at: datetime | None


class AppealDecisionBody(BaseModel):
    """Record the admin's appeal decision (upheld keeps it; overturned lifts it)."""

    decision: Literal["upheld", "overturned"]


class DisputeDecisionBody(BaseModel):
    """Register an administrative dispute decision (NO financial effect — Phase 15)."""

    outcome: Literal["procedente", "improcedente"]
    note: str | None = Field(default=None, max_length=500)


class DisputeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    delivery_id: int
    courier_id: int
    status: str
    reason: str | None
    opened_at: datetime
