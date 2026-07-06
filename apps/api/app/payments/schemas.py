"""Payment request/response schemas (pydantic v2, `extra='forbid'` — A03).

`card_blob` is an OPAQUE base64 string (the RSA-OAEP ciphertext from the client) — the
schema NEVER has raw card fields (`numeroCartao`/`cvv`), so a mass-assignment of card
data is impossible by construction (A09). Money is integer cents in every response.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PublicKeyOut(_Strict):
    """The RSA public key PEM served to the client (so it can encrypt the card)."""

    public_key: str


class SubscribeBody(_Strict):
    """Activate a plan by card (RSA blob) or PIX automático (no card)."""

    plan_id: int
    cycle: Literal["mensal", "anual"] = "mensal"
    method: Literal["card", "pix"]
    # Opaque RSA-OAEP ciphertext of {nomeTitular,numeroCartao,validade,cvv}. card only.
    card_blob: str | None = Field(default=None, max_length=4096)
    # PIX only: enables PIX Automático BACEN (recurring debit authorization).
    # False = one-time QR code; True = recurring authorization via /v3/pix/automatic.
    pix_recorrente: bool = False


class SubscriptionOut(_Strict):
    """The subscription state surfaced to the store (no token, no card)."""

    subscription_id: int
    billing_status: str
    payment_method: str | None
    plan_id: int
    amount_cents: int
    next_due_at: str | None
    qr_code: str | None = None
    qr_code_base64: str | None = None
    pix_autorizacao_status: str | None = None  # CRIADA | APROVADA | EXPIRADA | CANCELADA


class ChargeHistoryItem(_Strict):
    """One charge row for the history table (mono values in the UI)."""

    id: int
    kind: str
    amount_cents: int
    method: str
    status: str
    transaction_id: str | None
    created_at: str | None
    due_at: str | None = None


class PlanChangeBody(_Strict):
    """Upgrade (pro-rata now) or downgrade (scheduled) to a target plan (RN-029)."""

    target_plan_id: int


class PlanChangeOut(_Strict):
    kind: Literal["upgrade", "downgrade", "noop"]
    charged_cents: int
    effective: str  # "now" | "cycle_end"
