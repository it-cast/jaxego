"""Merchant + plans API contracts (Pydantic v2, extra='forbid' — A03).

These schemas are the stable contract the wizard (apps/web) consumes (Integration
contracts). Document validation uses `validate-docbr` (T-13) — never hand-rolled
(Pitfall 5: CNPJ alphanumeric, jul/2026). `normalize_document` keeps alphanumeric
characters (uppercase) so the new CNPJ format survives normalisation.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from validate_docbr import CNPJ, CPF

from app.auth.schemas import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH

_CNPJ = CNPJ()
_CPF = CPF()


def normalize_document(raw: str) -> str:
    """Strip mask, keep alphanumerics, uppercase (CNPJ alphanumeric jul/2026)."""
    return "".join(c for c in raw if c.isalnum()).upper()


def validate_document(raw: str, *, account_type: str) -> bool:
    """Server-side check-digit validation via validate-docbr (TH-08)."""
    digits = normalize_document(raw)
    if account_type == "cnpj":
        return _CNPJ.validate(digits)
    return _CPF.validate(digits)


class MerchantSignupBody(BaseModel):
    """F-01 signup contract. `extra='forbid'` blocks mass assignment (A03)."""

    model_config = ConfigDict(extra="forbid")

    account_type: Literal["cnpj", "cpf"]
    document: str = Field(min_length=3, max_length=20)
    trade_name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=40)
    # E.164: +55 + DDD + number. Kept as a string; validated by pattern.
    phone_e164: str = Field(min_length=12, max_length=20, pattern=r"^\+\d{11,15}$")
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    # LGPD: explicit, non-pre-checked consent is required to submit (TH-09).
    consent: bool
    # Optional chosen plan; defaults to Free. A paid plan -> pending_payment (E3).
    plan_code: str | None = Field(default=None, max_length=32)

    @field_validator("document")
    @classmethod
    def _normalize_doc(cls, v: str) -> str:
        # Normalise here; full check-digit validation runs in the service (it
        # needs account_type, which field-level validation cannot see reliably).
        return normalize_document(v)

    @field_validator("consent")
    @classmethod
    def _consent_required(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("consent_required")
        return v


class SignupResponse(BaseModel):
    """Response shape consumed by the wizard (Integration contracts)."""

    model_config = ConfigDict(extra="forbid")

    merchant_id: int
    status: Literal["pending_payment", "pending_validation", "active", "suspended"]
    next_step: Literal["confirm", "done"]


class ConfirmPhoneBody(BaseModel):
    """OTP confirmation for a merchant phone."""

    model_config = ConfigDict(extra="forbid")

    otp: str = Field(min_length=6, max_length=6)


class ConfirmPhoneResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmed: bool


class ConfirmEmailBody(BaseModel):
    """E-mail confirmation by token (link)."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=8, max_length=128)


class InterestBody(BaseModel):
    """ "Ainda não chegamos aí" interest capture (LGPD consent — TH-09)."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    cidade: str = Field(min_length=2, max_length=120)
    consent: bool

    @field_validator("consent")
    @classmethod
    def _consent_required(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("consent_required")
        return v


class PlanRead(BaseModel):
    """A subscription plan projection (values from the SEED — DRV-009)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    codename: str
    nome: str
    preco_cents: int
    entregas_mes: int
    taxa_entrega_cents: int
    is_free: bool
    is_unlimited: bool


def mask_document_display(doc: str) -> str:
    """Mask a CPF/CNPJ for admin display: keep first 2 + last 2 (TH-06)."""
    digits = "".join(ch for ch in doc if ch.isdigit())
    if len(digits) < 4:
        return "***"
    return f"{digits[:2]}•••{digits[-2:]}"


class MerchantAdminListItem(BaseModel):
    """One store row in the area admin's list (F2.4). Document masked (TH-06)."""

    model_config = ConfigDict(extra="forbid")

    id: int
    trade_name: str
    account_type: str
    document_masked: str
    category: str | None
    status: str
    created_at: str | None


class MerchantAdminListOut(BaseModel):
    """Paginated area store list (single query + COUNT — no N+1)."""

    model_config = ConfigDict(extra="forbid")

    items: list[MerchantAdminListItem]
    total: int
    limit: int
    offset: int
