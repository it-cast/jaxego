"""DeliveryLocation — courier position samples for live tracking (DEC-002 / LGPD).

Area-scoped. The courier app posts a sample every 60-120s WHILE the delivery is in
the moving window (ACEITA→COLETADA). Minimisation: ONLY lat/lng + `recorded_at`
(aware-UTC, TD-010) — no accuracy/heading/speed, no permanent movement trail. The
`recorded_at` index backs the 24h purge job (`purge_locations` — TH-4 / Pitfall 3):
samples of terminal deliveries older than 24h are HARD-deleted (retention, LGPD).
There is NO TimestampMixin (a sample is never updated; `recorded_at` is the only time).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin


class DeliveryLocation(Base, AreaScopedMixin):
    """A single courier position sample (lat/lng only — minimisation, TH-4)."""

    __tablename__ = "delivery_locations"
    __table_args__ = (
        # Latest-position lookup for the public tracker (delivery_id, recorded_at).
        Index("ix_delivery_locations_delivery_id_recorded_at", "delivery_id", "recorded_at"),
        # Retention purge sweeps by recorded_at (Pitfall 3 / TH-4).
        Index("ix_delivery_locations_recorded_at", "recorded_at"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("deliveries.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
