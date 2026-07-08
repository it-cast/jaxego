"""SubscriptionPlan model — GLOBAL catalog (DRV-009).

Plans are catalog data, not area-scoped: a plan is offered platform-wide, a
*subscription* (merchant_subscriptions) is what carries area_id. Values
(price, monthly deliveries, per-delivery fee) live in the SEED (`tools/seed.py`),
NEVER hardcoded in code or UI (DRV-009). `is_free` marks the immutable Free plan.
Money is stored as integer cents (no float) — `price_monthly_cents`, `price_annual_cents`, `fee_cents`.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, TimestampMixin


class SubscriptionPlan(Base, TimestampMixin):
    """A subscription tier. `code` is the natural key (seed upsert / RN-009)."""

    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    # Natural key for idempotent seed upsert (Free/Início/Profissional/Sem Limite).
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    # Monetary values as integer cents (DRV-009 — seed-editable, never hardcoded).
    price_monthly_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price_annual_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deliveries_per_month: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Per-delivery fee in cents (-1 sentinel reserved for "unlimited" tiers if needed).
    fee_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # True only for the immutable Free plan (seed marks it; app refuses to mutate).
    is_free: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Free has unlimited months but a hard delivery cap; this flags the no-cap tier.
    is_unlimited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
