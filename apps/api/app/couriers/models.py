"""Courier + CourierDocument models (F-02, D-08 / ADR-011 / ADR-004).

`Courier` is AREA-SCOPED (AreaScopedMixin): a delivery person is bound to exactly
one area (D-02). The SAME CPF may onboard in SEVERAL areas (one row per area —
new vínculo), but a duplicate in the SAME area is blocked by the composite UNIQUE
(`area_id`, `cpf`) — this is the structural enforcement of F-02 E2
(anti-enumeration; the service returns a single generic message). `status` is the
state machine (D-08); `mei_pending` (RN-024) records that the courier has no
active MEI and may therefore only work the "direct" payment flow.

`CourierDocument` carries the per-item KYC status (D-04): each document is
approved/rejected INDEPENDENTLY (E4 — rejecting the CNH never invalidates an
already-approved selfie). It stores the B2 `storage_key`, the SHA-256 of the
REPROCESSED derivative (anti-tamper, TH-07), the `expires_at` for documents that
expire (CNH/CRLV/MEI — job transitions them), and `anonymized_at`/`deleted_at`
nullable from day one (RN-021 / LGPD, reachable by Phase 14 jobs).

PII (cpf, mei_cnpj) is masked in outputs and NEVER logged (TH-05). The storage
key is generated server-side and contains NO CPF (TH-11).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin

# Coverage row kinds (Pattern 3 — RN-003).
COVERAGE_KINDS = ("include", "exclude")

# Pricing modes (A3): per-neighborhood OR per-km band.
PRICING_MODES = ("neighborhood", "km")

# Courier state machine values (D-08). Transitions live in `state_machine.py`.
COURIER_STATUSES = ("pending_kyc", "active", "suspended", "banned")

# Vehicle types (D-01 etapa 3). "moto"/"carro" require a plate (Mercosul).
VEHICLE_TYPES = ("moto", "bicicleta", "carro", "a_pe")

# Document kinds (D-01 / D-03). selfie is always required (simples); cnh/crlv/mei/
# antecedentes only when the area requires COMPLETA.
DOCUMENT_KINDS = ("selfie", "cnh", "crlv", "mei", "antecedentes")

# Per-item document status (D-04). pending_upload -> pending (after reprocess) ->
# approved | rejected; approved -> expired (job); rejected/expired -> re-upload.
DOCUMENT_STATUSES = (
    "pending_upload",
    "pending",
    "approved",
    "rejected",
    "expired",
)


class Courier(Base, AreaScopedMixin, TimestampMixin):
    """A delivery person (F-02). Area-scoped; status is the state machine (D-08)."""

    __tablename__ = "couriers"
    __table_args__ = (
        # F-02 E2: same user cannot onboard twice in the SAME area.
        UniqueConstraint("area_id", "user_id", name="uq_couriers_area_id_user_id"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)

    # Owner User. CPF lives in users (unique global). One user may have several
    # courier rows across areas (F-02 E2).
    user_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    # [PII] E.164 phone — masked in outputs, never logged.
    phone_e164: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)  # [PII]

    # KYC level required by the area at submit time ("simples" | "completa").
    kyc_level: Mapped[str] = mapped_column(String(16), nullable=False, default="simples")

    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending_kyc")

    # Vehicle (D-01 etapa 3). plate nullable (bicycle / on-foot have none).
    vehicle_type: Mapped[str] = mapped_column(String(16), nullable=False, default="moto")
    vehicle_plate: Mapped[str | None] = mapped_column(String(8), nullable=True)

    # MEI (RN-024). mei_pending=True => may only work the "direct" payment flow;
    # a permanent regularisation banner is shown. mei_cnpj [PII-ish] — never logged.
    mei_cnpj: Mapped[str | None] = mapped_column(String(14), nullable=True)
    mei_pending: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Safe2Pay subaccount/recipient id (Phase 10, RN-010): set when the MEI is approved
    # so the delivery split can pay the courier's corrida. NULL → no platform repasse.
    s2p_recipient_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Team (every courier must belong to a team).
    team_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("teams.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
        default=0,
    )

    # Availability (Phase 6, D-06): online/offline is persisted; `busy` is DERIVED
    # from the load (active deliveries vs max_concurrent) — NOT a column. Only an
    # `active` courier may go online (guarded in availability.py).
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_concurrent: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # LGPD retention bookkeeping (RN-021) — reachable by Phase 14 jobs.
    anonymized_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)


class CourierDocument(Base, AreaScopedMixin, TimestampMixin):
    """One KYC document with an INDEPENDENT per-item status (D-04 / E4).

    Area-scoped (carries area_id) so the admin queue / view-url query can filter
    by `area_id = scope` directly in the WHERE clause (TH-03 — IDOR → 404).
    """

    __tablename__ = "courier_documents"
    __table_args__ = (
        # Eager filtering for the admin queue / per-courier item list (Gate 8 —
        # no N+1; one query loads a courier's documents by status).
        Index("ix_courier_documents_courier_id_status", "courier_id", "status"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)

    courier_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )

    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending_upload")

    # B2 object key (server-side, ULID-based, NO CPF — TH-11). Nullable until the
    # presign is issued. content_type is the DERIVATIVE's (always image/webp here).
    storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # SHA-256 (hex) of the REPROCESSED derivative — anti-tamper source of truth
    # (TH-07). The client-declared sha256 of the raw is kept transiently only.
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sha256_client: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Rejection reason (D-04): an enum slug + free-text detail. Both nullable
    # (only set on rejection). Reject without a reason is blocked at the service.
    reject_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reject_detail: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Expiry for documents that expire (CNH/CRLV/MEI). aware-UTC (TD-010); a job
    # transitions expired documents back to re-upload. Indexed for the batch sweep.
    expires_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True, index=True)

    # First time the document entered `pending` (escalation 48h clock — E5).
    submitted_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)

    # LGPD retention (RN-021) — reachable by Phase 14 jobs.
    anonymized_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)


class CourierCoverageArea(Base, AreaScopedMixin, TimestampMixin):
    """The neighborhoods a courier serves / refuses (RN-003, REQ-016).

    Area-scoped; `kind` is 'include' | 'exclude'. UNIQUE (courier_id,
    neighborhood_id) → one row per neighborhood per courier. Eligibility requires
    coverage at BOTH the pickup and the dropoff (see coverage.is_eligible).
    """

    __tablename__ = "courier_coverage_areas"
    __table_args__ = (
        UniqueConstraint(
            "courier_id",
            "neighborhood_id",
            name="uq_courier_coverage_areas_courier_id_neighborhood_id",
        ),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    courier_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    neighborhood_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("neighborhoods_catalog.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(8), nullable=False)


class CourierPricingTable(Base, AreaScopedMixin, TimestampMixin):
    """The courier's freight table (RN-015, REQ-017) — by neighborhood OR by km.

    The platform NEVER fixes the price; it only imposes the area floor (validated
    in pricing.py). `price`/`up_to_km`/`return_pct` are `Numeric` (never Float).
    `neighborhood_id` is set only in mode 'neighborhood'; `up_to_km` only in mode
    'km'.
    """

    __tablename__ = "courier_pricing_tables"
    __table_args__ = (
        Index("ix_courier_pricing_tables_courier_id_mode", "courier_id", "mode"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    courier_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    neighborhood_id: Mapped[int | None] = mapped_column(
        BIG_ID,
        ForeignKey("neighborhoods_catalog.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    up_to_km: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    return_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
