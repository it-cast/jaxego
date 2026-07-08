"""Courier signup + document API contracts (Pydantic v2, extra='forbid' — A03).

These are the stable contracts the Ionic wizard (apps/web) and the admin panel
consume (Integration contracts). CPF validation uses `validate-docbr` (never
hand-rolled). The request body carries PII (CPF, phone, email) and is NEVER
logged (TH-05).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from validate_docbr import CPF

from app.auth.schemas import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH

_CPF = CPF()

DocumentKind = Literal["selfie", "cnh", "crlv", "mei", "antecedentes"]
VehicleType = Literal["moto", "bicicleta", "carro", "a_pe"]
CourierStatus = Literal["pending_kyc", "active", "suspended", "banned"]
RejectReason = Literal["ilegivel", "sem_ear", "vencida", "nao_confere", "outro"]


def normalize_cpf(raw: str) -> str:
    """Strip mask, keep digits only."""
    return "".join(c for c in raw if c.isdigit())


def validate_cpf(raw: str) -> bool:
    """Server-side CPF check-digit validation (TH-08)."""
    return _CPF.validate(normalize_cpf(raw))


# ---------------------------------------------------------------------------
# Signup (wizard step 1 — área + dados). Creates User + Courier (pending_kyc).
# ---------------------------------------------------------------------------
class CourierSignupBody(BaseModel):
    """F-02 step 1 contract. `extra='forbid'` blocks mass assignment (A03)."""

    model_config = ConfigDict(extra="forbid")

    area_id: int
    cpf: str = Field(min_length=11, max_length=14)
    full_name: str = Field(min_length=2, max_length=120)
    phone_e164: str = Field(min_length=12, max_length=20, pattern=r"^\+\d{11,15}$")
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    vehicle_type: VehicleType
    vehicle_plate: str | None = Field(default=None, max_length=8)
    team_id: int = Field(gt=0)
    # LGPD: explicit, non-pre-checked consent is required to submit (TH-09).
    consent: bool

    @field_validator("cpf")
    @classmethod
    def _normalize_cpf(cls, v: str) -> str:
        return normalize_cpf(v)

    @field_validator("consent")
    @classmethod
    def _consent_required(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("consent_required")
        return v


class CourierSignupResponse(BaseModel):
    """Response consumed by the wizard (Integration contracts)."""

    model_config = ConfigDict(extra="forbid")

    courier_id: int
    status: CourierStatus
    kyc_level: Literal["simples", "completa"]
    next_step: Literal["selfie", "documents", "done"]


# ---------------------------------------------------------------------------
# Document presign + complete (wizard steps 2/4).
# ---------------------------------------------------------------------------
class DocumentPresignBody(BaseModel):
    """Request a presigned PUT for a document upload."""

    model_config = ConfigDict(extra="forbid")

    kind: DocumentKind
    # The client declares the SHA-256 of the RAW file (detects transport
    # corruption). The server confirms the derivative's hash (source of truth).
    sha256_client: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    content_type: Literal["image/jpeg", "image/png", "image/webp"]


class DocumentPresignResponse(BaseModel):
    """Presigned PUT envelope the doc-upload component uses."""

    model_config = ConfigDict(extra="forbid")

    document_id: int
    presigned_url: str
    method: Literal["PUT"]
    expires_in: int
    headers: dict[str, str]


class DocumentReadResponse(BaseModel):
    """A document's current KYC state (read by the wizard / admin)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    kind: DocumentKind
    status: Literal["pending_upload", "pending", "approved", "rejected", "expired"]
    reject_reason: RejectReason | None = None
    reject_detail: str | None = None


# ---------------------------------------------------------------------------
# MEI (wizard step 4 — optional). Absence/inactive → mei_pending (RN-024).
# ---------------------------------------------------------------------------
class MeiBody(BaseModel):
    """Submit a MEI CNPJ for Receita validation (D-07)."""

    model_config = ConfigDict(extra="forbid")

    cnpj: str = Field(min_length=14, max_length=18)

    @field_validator("cnpj")
    @classmethod
    def _normalize(cls, v: str) -> str:
        return "".join(c for c in v if c.isalnum()).upper()


class MeiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mei_pending: bool


# ---------------------------------------------------------------------------
# Admin: view-url + item-a-item review (T-06).
# ---------------------------------------------------------------------------
class ViewUrlResponse(BaseModel):
    """Short-lived presigned GET for the admin viewer (≤180s)."""

    model_config = ConfigDict(extra="forbid")

    url: str
    expires_in: int


class DocumentReviewBody(BaseModel):
    """Approve or reject a document item-a-item (D-04)."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["approve", "reject"]
    # Required when action == reject (validated in the service — a reject without
    # a reason is blocked, the wizard shows "Selecione o motivo antes de reprovar").
    reason: RejectReason | None = None
    detail: str | None = Field(default=None, max_length=500)


class DocumentReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: int
    status: Literal["approved", "rejected"]
    courier_status: CourierStatus


# ---------------------------------------------------------------------------
# Phase 6 — coverage / pricing / availability (área operável)
# ---------------------------------------------------------------------------
PricingMode = Literal["neighborhood", "km"]


class CoverageBody(BaseModel):
    """The neighborhoods the courier serves (include) / refuses (exclude)."""

    model_config = ConfigDict(extra="forbid")

    includes: list[int] = Field(default_factory=list)
    excludes: list[int] = Field(default_factory=list)


class CoverageRowRead(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    neighborhood_id: int
    kind: Literal["include", "exclude"]


class PricingRow(BaseModel):
    """One freight-table row. `price`/`return_pct` are Decimal (never float)."""

    model_config = ConfigDict(extra="forbid")

    neighborhood_id: int | None = None
    up_to_km: Decimal | None = Field(default=None, ge=0)
    price: Decimal = Field(ge=0)
    # % return on the run — 0..100 (Security item 4).
    return_pct: int | None = Field(default=None, ge=0, le=100)


class PricingBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: PricingMode
    rows: list[PricingRow] = Field(default_factory=list)


class PricingRowRead(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    mode: PricingMode
    neighborhood_id: int | None
    up_to_km: Decimal | None
    price: Decimal
    return_pct: Decimal | None


class AvailabilityBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    online: bool
    online_until: datetime | None = None


class CourierLocationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_online: bool
    busy: bool
    online_until: datetime | None = None


def mask_cpf_display(cpf: str) -> str:
    """Mask a CPF for admin display: keep first 3 + last 2 (123.***.***-09)."""
    digits = normalize_cpf(cpf)
    if len(digits) < 5:
        return "***"
    return f"{digits[:3]}.***.***-{digits[-2:]}"


class CourierAdminListItem(BaseModel):
    """One courier row in the area admin's queue/list (F2.0). CPF masked (TH-05)."""

    model_config = ConfigDict(extra="forbid")

    id: int
    full_name: str
    cpf_masked: str
    status: str
    kyc_level: str
    created_at: str | None


class CourierAdminListOut(BaseModel):
    """Paginated area courier list (single query + COUNT — no N+1)."""

    model_config = ConfigDict(extra="forbid")

    items: list[CourierAdminListItem]
    total: int
    limit: int
    offset: int


class CourierDocumentItem(BaseModel):
    """One KYC document's kind + status (D-04) for the courier's own profile."""

    model_config = ConfigDict(extra="forbid")

    id: int
    kind: str
    status: str
    reject_reason: str | None = None
    reject_detail: str | None = None


class CourierDocumentAdminItem(BaseModel):
    """One KYC document for the admin detail view — includes ID for review/view-url."""

    model_config = ConfigDict(extra="forbid")

    id: int
    kind: str
    status: str
    reject_reason: str | None = None
    reject_detail: str | None = None
    created_at: str | None = None


class CourierAdminDetailOut(BaseModel):
    """Courier detail for the area admin KYC review page."""

    model_config = ConfigDict(extra="forbid")

    id: int
    full_name: str
    cpf_masked: str
    status: str
    kyc_level: str
    vehicle_type: str
    vehicle_plate: str | None = None
    created_at: str | None = None
    documents: list[CourierDocumentAdminItem]


class CourierProfileOut(BaseModel):
    """The courier's OWN profile (F1.6 — tpl-c-profile identity + documents).

    PII masked (TH-05): CPF/phone/e-mail never returned raw. The score lives in a
    separate endpoint (ADR-013). PIX key is not stored yet (F1.7 — needs migration).
    """

    model_config = ConfigDict(extra="forbid")

    id: int
    full_name: str
    cpf_masked: str
    phone_masked: str
    email_masked: str
    vehicle_type: str
    vehicle_plate: str | None
    kyc_level: str
    status: str
    is_online: bool
    online_until: datetime | None = None
    mei_pending: bool
    team_id: int
    team_name: str | None = None
    documents: list[CourierDocumentItem]
