"""CourierRating model (REQ-033 / D-03).

AREA-SCOPED. The store rates the courier AFTER the delivery is FINALIZADA (1-5 stars +
optional comment). UNIQUE per `delivery_id` → exactly one rating per delivery (append,
no edit/delete in M1). It feeds the `ratings` component of the score (weight from the
seed). `merchant_id` scopes who may rate (only the store that owns the delivery).
"""

from __future__ import annotations

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, AreaScopedMixin, TimestampMixin

# Valid star range (D-03). 1..5 inclusive — validated at the schema boundary.
RATING_MIN_STARS = 1
RATING_MAX_STARS = 5


class CourierRating(Base, AreaScopedMixin, TimestampMixin):
    """Store → courier rating after FINALIZADA (REQ-033). One per delivery."""

    __tablename__ = "courier_ratings"
    __table_args__ = (
        # One rating per delivery (D-03 — 1 por entrega).
        UniqueConstraint("delivery_id", name="uq_courier_ratings_delivery_id"),
        # The courier's rating history (score component aggregation) — no scan.
        Index("ix_courier_ratings_courier_id", "courier_id"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("deliveries.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    courier_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    merchant_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("merchants.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    stars: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
