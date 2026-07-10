from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PlanAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    price_monthly_cents: int
    price_annual_cents: int
    deliveries_per_month: int
    fee_cents: int
    taxa_pix_cents: int
    taxa_servico_cents: int
    is_free: bool
    is_unlimited: bool
    is_active: bool
    sort_order: int


class PlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=80)
    price_monthly_cents: int = Field(ge=0)
    price_annual_cents: int = Field(ge=0)
    deliveries_per_month: int = Field(ge=0)
    fee_cents: int = Field(ge=0, default=0)
    taxa_pix_cents: int = Field(ge=0, default=0)
    taxa_servico_cents: int = Field(ge=0, default=0)
    is_unlimited: bool = False
    sort_order: int = Field(ge=0, default=0)


class PlanUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=80)
    price_monthly_cents: int | None = Field(default=None, ge=0)
    price_annual_cents: int | None = Field(default=None, ge=0)
    deliveries_per_month: int | None = Field(default=None, ge=0)
    fee_cents: int | None = Field(default=None, ge=0)
    taxa_pix_cents: int | None = Field(default=None, ge=0)
    taxa_servico_cents: int | None = Field(default=None, ge=0)
    is_unlimited: bool | None = None
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)
