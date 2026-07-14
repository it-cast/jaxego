"""DeliveryLocation — append-only log of courier actions + location (audit trail).

Area-scoped. One row per real courier action on a delivery (aceitou, coletou,
chegou_destino, entregou, recusou_entrega — see `app/tracking/service.py` for
the canonical action names), carrying the courier's device GPS at that moment.
This is a PERMANENT audit log, not a live-tracking trail: there is no purge job
(CORRECAO-252 removed it — a previous design purged samples after 24h, back
when this table was an unused periodic-ping trail). A MySQL trigger
(`trg_dl_no_update`/`trg_dl_no_delete`, migration 0048) rejects UPDATE/DELETE —
same append-only guarantee as `delivery_state_transitions`. There is NO
TimestampMixin (a row is never updated; `recorded_at` is the only time).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin


class DeliveryLocation(Base, AreaScopedMixin):
    """One courier action + GPS position sample (append-only audit log)."""

    __tablename__ = "delivery_locations"
    __table_args__ = (
        # Timeline lookup for a single delivery (public tracker + admin audit view).
        Index("ix_delivery_locations_delivery_id_recorded_at", "delivery_id", "recorded_at"),
        # "What did this courier do" queries.
        Index("ix_delivery_locations_courier_id", "courier_id"),
        # "Every X action across deliveries" queries.
        Index("ix_delivery_locations_action", "action"),
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
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
