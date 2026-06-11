"""Public create-delivery contract (Pydantic v2, extra='forbid' — A03 / TH-02).

The integrator targets a store by `merchant_external_ref` (its own id for the
store) OR `merchant_id` (D-03), then carries the SAME delivery fields as the
internal create. Server-derived fields are absent (mass-assignment blocked). The
response mirrors the internal create response so a replay is byte-identical (D-04).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.deliveries.schemas import PaymentMethod, ProofMethod


class PublicCreateDeliveryBody(BaseModel):
    """F-04 public create. Targets a store by external_ref OR merchant_id (D-03)."""

    model_config = ConfigDict(extra="forbid")

    # --- Store target (exactly one of the two — D-03) ---
    merchant_external_ref: str | None = Field(default=None, max_length=120)
    merchant_id: int | None = Field(default=None, ge=1)

    # --- Pickup (store address) ---
    pickup_address: str = Field(min_length=3, max_length=255)
    pickup_neighborhood: str | None = Field(default=None, max_length=120)

    # --- Dropoff ---
    dropoff_neighborhood_id: int
    dropoff_address: str = Field(min_length=3, max_length=255)
    dropoff_number: str | None = Field(default=None, max_length=20)
    dropoff_complement: str | None = Field(default=None, max_length=120)
    distance_m: int | None = Field(default=None, ge=0)

    # --- Recipient (name + phone mandatory; email/CPF optional) ---
    recipient_name: str = Field(min_length=2, max_length=120)
    recipient_phone_e164: str = Field(min_length=12, max_length=20, pattern=r"^\+\d{11,15}$")
    recipient_email: EmailStr | None = None
    recipient_cpf: str | None = Field(default=None, max_length=14)

    # --- Items / reference ---
    items_description: str | None = Field(default=None, max_length=500)
    items_quantity: int = Field(default=1, ge=1, le=999)
    declared_value_cents: int | None = Field(default=None, ge=0)
    reference_number: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=500)

    # --- Choices (public API is `direct` only — card/pix carry payer fields the
    # public integrator does not own; kept out of the public contract) ---
    proof_method: ProofMethod = ProofMethod.photo
    payment_method: PaymentMethod = PaymentMethod.direct

    @model_validator(mode="after")
    def _require_one_store_target(self) -> PublicCreateDeliveryBody:
        if self.merchant_external_ref is None and self.merchant_id is None:
            raise ValueError("Informe merchant_external_ref ou merchant_id.")
        return self


class PublicDeliveryResponse(BaseModel):
    """Public create response — mirrors the internal create (replay-identical)."""

    delivery_id: int
    public_token: str
    state: str
    estimate_min_cents: int | None
    estimate_max_cents: int | None
    fee_cents: int
    no_couriers_warning: bool
