"""Platform-admin API schemas (REQ-046/047). Read-mostly; bound filters (TH-06)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AreaOverviewRow(BaseModel):
    """One area's headline counts for the platform overview (tela 23)."""

    area_id: int
    codename: str
    name: str
    couriers: int
    merchants: int
    deliveries: int


class CourierSearchRow(BaseModel):
    """A courier search result with its latest score level (tela 24)."""

    courier_id: int
    area_id: int
    full_name: str
    status: str
    score_total: float | None
    score_level: str | None


class MerchantSearchRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    merchant_id: int
    area_id: int
    name: str
    status: str


class RevenueShareRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    area_id: int
    share_pct: float
    effective_from: datetime


class RevenueShareBody(BaseModel):
    """Set the parametrised revenue-share % for an area (NO money moves — D-07)."""

    share_pct: float = Field(..., ge=0, le=100)
