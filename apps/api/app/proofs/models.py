"""DeliveryProof — photo proof of pickup/delivery/refusal (F-06 / RN-005).

Area-scoped. One row per proof attempt that produced a stored derivative. Records
the B2 key of the STRIPPED derivative (never the raw — the raw is read for GPS then
discarded), the geofence verdict, the `low_confidence` flag (set after 3 failed
geofence checks — ADR-008 / RN-005), and the method (pickup/delivery/refusal). The
GPS used for the geofence is gravado na `delivery_state_transition` (RN-012) — NOT
here as authority; `geofence_ok`/`low_confidence` are the durable verdict.

`proof_kind` ∈ {pickup, delivery, refusal}. `method` ∈ {photo, photo_reference}
(otp is "em breve" — TD-003). aware-UTC `created_at` (TD-010).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin

PROOF_KINDS = ("pickup", "delivery", "refusal")


class DeliveryProof(Base, AreaScopedMixin, TimestampMixin):
    """A stored proof derivative + its geofence verdict (F-06 / TH-1)."""

    __tablename__ = "delivery_proofs"
    __table_args__ = (
        Index("ix_delivery_proofs_delivery_id", "delivery_id"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("deliveries.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    # pickup | delivery | refusal
    proof_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    # photo | photo_reference
    method: Mapped[str] = mapped_column(String(16), nullable=False, default="photo")
    # B2 key of the STRIPPED WebP derivative (never the raw). NULL for photo_reference.
    storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # SHA-256 of the stored derivative (anti-tamper — reuse media pipeline).
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Geofence verdict (the durable truth; the GPS itself lives in the transition).
    geofence_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    low_confidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # The GPS that was validated (kept for the proof record; auditoria = transition).
    gps_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    refusal_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
