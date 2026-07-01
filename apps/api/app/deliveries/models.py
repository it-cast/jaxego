"""Delivery + DeliveryStateTransition + Recipient models (F-03 / D-04 / D-08).

`Delivery` is AREA-SCOPED (AreaScopedMixin): every delivery belongs to exactly one
area and one merchant. `courier_id` is NULL until acceptance (Phase 8 — the
delivery is born CRIADA with no courier). `state` is the 7-state machine (RN-019);
the ONLY writer of `state` is `service.transition()`. Money is stored as INTEGER
CENTS (never Float) — `estimate_min_cents` / `estimate_max_cents` / `fee_cents`.

RN-013 — privacy boundary, modelled structurally so the Phase 8 offer serializer
can be built WITHOUT the full dropoff address by construction, not by a forgettable
filter:
  - FULL address (revealed only AFTER pickup): `dropoff_address` / `dropoff_number`
    / `dropoff_complement`.
  - Revealed BEFORE pickup (offer): `dropoff_neighborhood_id` + `distance_m`.

`DeliveryStateTransition` is APPEND-ONLY (D-04 / RN-012): a MySQL trigger rejects
UPDATE/DELETE (`SIGNAL 45000`). Each row records from/to state, actor, reason, IP,
and GPS when present, with an aware-UTC `created_at` (TD-010).

`Recipient` (D-08 / LGPD) carries identity SEPARATE from the address: name + phone
(mandatory — base legal: execução de contrato), email/CPF optional. The CPF is
stored ONLY as `cpf_hash` (SHA-256) — the model has NO raw-CPF column. PII is
masked in outputs and NEVER logged (TH-04/TH-05). `anonymized_at` is reachable by
the Phase 14 retention job (RN-021).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin

# The 9 canonical delivery states (RN-019 / D-03). Transitions live in
# `state_machine.py`. AGENDADA is the initial state for scheduled deliveries;
# Inngest transitions it to CRIADA at the scheduled time. SEM_RESPOSTA is
# reached when the dispatch cascade exhausts every eligible courier.
DELIVERY_STATES = (
    "AGENDADA",
    "CRIADA",
    "SEM_RESPOSTA",
    "ACEITA",
    "COLETADA",
    "ENTREGUE",
    "RECUSADA_NO_DESTINO",
    "CANCELADA",
    "FINALIZADA",
)

# Per-delivery payment method (RN-023 / D-02). Only `direct` is enabled in Phase 7;
# `card`/`pix` are accepted by the enum but rejected by the rule ("em breve").
PAYMENT_METHODS = ("direct", "card", "pix")

# Proof-of-delivery method (D-01). Only `photo` active here; `otp` is "em breve".
PROOF_METHODS = ("photo", "photo_reference", "otp")

# Dispatch mode (Phase 8 will add cascade/broadcast); `direct` placeholder here.
DISPATCH_MODES = ("direct",)


class Delivery(Base, AreaScopedMixin, TimestampMixin):
    """A delivery (F-03). Area-scoped; `state` is the state machine (RN-019)."""

    __tablename__ = "deliveries"
    __table_args__ = (
        # COUNT for the plan limit (RN-028) + the store list (screen 14) — no scan.
        Index(
            "ix_deliveries_area_id_merchant_id_created_at",
            "area_id",
            "merchant_id",
            "created_at",
        ),
        # Dispatch sweep (Phase 8) — find CRIADA deliveries by area/state.
        Index("ix_deliveries_area_id_state", "area_id", "state"),
        # Public tracking token (Phase 9) — opaque, non-sequential (A01).
        UniqueConstraint("public_token", name="uq_deliveries_public_token"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)

    merchant_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("merchants.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    # NULL until acceptance (Phase 8). No courier is bound while CRIADA (RN-013).
    courier_id: Mapped[int | None] = mapped_column(
        BIG_ID,
        ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
        index=True,
    )
    recipient_id: Mapped[int | None] = mapped_column(
        BIG_ID,
        ForeignKey("recipients.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
        index=True,
    )

    # State machine (RN-019). Default CRIADA; only transition() writes this.
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="CRIADA")
    dispatch_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="direct")
    payment_method: Mapped[str] = mapped_column(String(16), nullable=False, default="direct")
    proof_method: Mapped[str] = mapped_column(String(16), nullable=False, default="photo")

    # --- Pickup (the store's own address — revealed freely) ---
    pickup_address: Mapped[str] = mapped_column(String(255), nullable=False)
    pickup_neighborhood: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pickup_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    pickup_lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- Dropoff: RN-013 separation ---------------------------------------
    # FULL address — revealed to the courier ONLY after pickup (Phase 9).
    dropoff_address: Mapped[str] = mapped_column(String(255), nullable=False)
    dropoff_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dropoff_complement: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Revealed BEFORE pickup (the offer, Phase 8): neighborhood + distance only.
    dropoff_neighborhood_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("neighborhoods_catalog.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    dropoff_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    dropoff_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_m: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # --- Money (integer cents — never Float) ---
    price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # The platform fee accrues to the monthly invoice (Phase 11); 0 until priced.
    fee_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Items / reference ---
    items_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    items_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    declared_value_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Package size/weight (MG-1) — optional; drives multi-vehicle parity.
    weight_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    length_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    width_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Target teams (JSON array of team IDs — at least one required).
    team_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Product image (optional, uploaded by the store).
    image_key: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Opaque, non-sequential token for public tracking (Phase 9 — A01). ULID-like.
    public_token: Mapped[str] = mapped_column(String(32), nullable=False)
    # Origin of this delivery (manual create here; api/import later).
    origin: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")

    # Per-transition timestamps (aware-UTC; filled by Phases 8/9). Born with none.
    accepted_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    collected_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    finalized_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)

    # Cancellation bookkeeping (who/why) — reason/actor set on cancel.
    cancel_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cancel_actor_user_id: Mapped[int | None] = mapped_column(BIG_ID, nullable=True)
    # RN-004 cancellation cost in cents, computed server-side by state at cancel
    # time and RECORDED here (the effective charge is the Phase 11 invoice). Phase 9.
    cancel_cost_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    courier_collection_method: Mapped[str | None] = mapped_column(String(16), nullable=True)
    receipt_method: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # Scheduled dispatch (Inngest integration). NULL = immediate delivery.
    # `scheduled_at` is the intended dispatch time (aware UTC). Inngest fires a
    # webhook at this time to transition AGENDADA → CRIADA + enqueue_dispatch.
    # `inngest_event_id` is stored for dashboard traceability / debugging.
    scheduled_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    inngest_event_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # LGPD retention (RN-021) — reachable by Phase 14 jobs.
    anonymized_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)


class DeliveryStateTransition(Base, AreaScopedMixin):
    """Append-only history of state transitions (D-04 / RN-012 / TH-02).

    INSERT-only — a MySQL trigger rejects UPDATE/DELETE (`SIGNAL 45000`). No
    TimestampMixin (no `updated_at` — the row is never updated). `created_at` is
    aware UTC (TD-010), written by `transition()`.
    """

    __tablename__ = "delivery_state_transitions"
    __table_args__ = (
        Index("ix_delivery_state_transitions_delivery_id", "delivery_id"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("deliveries.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    # NULL on the initial CRIADA row (no prior state).
    from_state: Mapped[str | None] = mapped_column(String(24), nullable=True)
    to_state: Mapped[str] = mapped_column(String(24), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(BIG_ID, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gps_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)


class Recipient(Base, AreaScopedMixin, TimestampMixin):
    """Delivery recipient identity, separate from the address (D-08 / LGPD).

    Minimisation: `name` + `phone_e164` are mandatory (base legal: execução de
    contrato). `email`/`cpf_hash` are optional. The CPF is stored ONLY as a
    SHA-256 hash — there is NO raw-CPF column. PII is masked in outputs and never
    logged (TH-04/TH-05). `anonymized_at` is reachable by the Phase 14 job.
    """

    __tablename__ = "recipients"
    __table_args__ = (
        # Antifraude correlation by hashed CPF within an area (RN-005 / D-08).
        Index("ix_recipients_area_id_cpf_hash", "area_id", "cpf_hash"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)  # [PII]
    phone_e164: Mapped[str] = mapped_column(String(20), nullable=False)  # [PII]
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)  # [PII]
    # SHA-256 hex of the normalised CPF — NEVER the raw CPF (D-08 / TH-05).
    cpf_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Antifraude counters (RN-005) — incremented across deliveries/refusals.
    deliveries_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    refusals_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # LGPD retention (RN-021).
    anonymized_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
