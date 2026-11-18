"""Public create-delivery contract (Pydantic v2, extra='forbid' — A03 / TH-02).

The integrator targets a store by `merchant_external_ref` (its own id for the
store) OR `merchant_id` (D-03), then carries the SAME delivery fields as the
internal create. Server-derived fields are absent (mass-assignment blocked). The
response mirrors the internal create response so a replay is byte-identical (D-04).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

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

    pickup_lat: float | None = Field(default=None, ge=-90, le=90)
    pickup_lng: float | None = Field(default=None, ge=-180, le=180)

    # --- Dropoff (bairro pelo id do catálogo OU pelo nome, casado sem acento/caixa) ---
    dropoff_neighborhood_id: int | None = Field(default=None, ge=1)
    dropoff_neighborhood_name: str | None = Field(default=None, min_length=2, max_length=120)
    dropoff_address: str = Field(min_length=3, max_length=255)
    dropoff_number: str | None = Field(default=None, max_length=20)
    dropoff_complement: str | None = Field(default=None, max_length=120)
    dropoff_reference: str | None = Field(default=None, max_length=255)
    cep: str | None = Field(default=None, max_length=9)
    dropoff_lat: float | None = Field(default=None, ge=-90, le=90)
    dropoff_lng: float | None = Field(default=None, ge=-180, le=180)
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
        if (
            self.dropoff_neighborhood_id is None
            and not (self.dropoff_neighborhood_name or "").strip()
        ):
            raise ValueError("Informe dropoff_neighborhood_id ou dropoff_neighborhood_name.")
        if (self.pickup_lat is None) != (self.pickup_lng is None) or (self.dropoff_lat is None) != (
            self.dropoff_lng is None
        ):
            raise ValueError("Coordenadas vão em par (lat e lng).")
        return self


class PublicDeliveryResponse(BaseModel):
    """Public create response — mirrors the internal create (replay-identical)."""

    delivery_id: int
    public_token: str
    # Link público de acompanhamento (None sem PUBLIC_WEB_BASE_URL). Default None: um replay
    # de snapshot gravado antes deste campo continua válido.
    tracking_url: str | None = None
    state: str
    price_cents: int | None = None
    fee_cents: int
    no_couriers_warning: bool


# ---------------------------------------------------------------------------
# Vínculo da loja, cotação, consulta e cancelamento (integração Menu Certo).
# ---------------------------------------------------------------------------
class ResolveMerchantBody(BaseModel):
    """Acha a loja da ÁREA da chave pelo CNPJ/CPF (só dígitos são considerados)."""

    model_config = ConfigDict(extra="forbid")

    document: str = Field(min_length=11, max_length=20)


class PublicMerchantOut(BaseModel):
    merchant_id: int
    trade_name: str
    status: str
    external_ref: str | None = None
    # Acesso da loja ao Jaxegô: "disabled" quando a assinatura está bloqueada/cancelada
    access: str | None = None


class PublicQuoteOut(BaseModel):
    dropoff_neighborhood_id: int
    zona_name: str | None = None
    courier_count: int
    price_min_cents: int | None = None
    price_max_cents: int | None = None


class PublicPoint(BaseModel):
    lat: float
    lng: float


class PublicCourierOut(BaseModel):
    name: str
    phone_e164: str | None = None
    vehicle_type: str | None = None
    vehicle_plate: str | None = None
    rating: float | None = None


class PublicTimelineItem(BaseModel):
    state: str
    at: str | None = None


class PublicDeliveryDetail(BaseModel):
    """Estado completo de uma entrega da área (sem dados do destinatário)."""

    delivery_id: int
    public_token: str
    tracking_url: str | None = None
    reference_number: str | None = None
    state: str
    price_cents: int | None = None
    fee_cents: int
    cancelable: bool
    courier: PublicCourierOut | None = None
    courier_position: PublicPoint | None = None
    courier_position_at: str | None = None
    pickup: PublicPoint | None = None
    dropoff: PublicPoint | None = None
    dropoff_neighborhood: str | None = None
    timeline: list[PublicTimelineItem] = []
    created_at: str | None = None


class PublicCancelBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=255)


# ---------------------------------------------------------------------------
# Cadastro da loja pelo integrador (Menu Certo) e acesso da loja — escopo merchants:write.
# A área vem da chave; o plano é pago pelo integrador (assinatura ativa, sem cobrança aqui).
# ---------------------------------------------------------------------------
class PublicCreateMerchantBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_type: Literal["cnpj", "cpf"]
    document: str = Field(min_length=11, max_length=20)
    trade_name: str = Field(min_length=2, max_length=120)
    category: Literal["restaurante", "comercio", "farmacia", "mercado", "outro"] = "restaurante"
    phone_e164: str = Field(min_length=12, max_length=20, pattern=r"^\+\d{11,15}$")
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    plan_code: str = Field(min_length=2, max_length=32)
    # Consentimento LGPD colhido pelo integrador (a loja autorizou o cadastro)
    consent: bool
    external_ref: str | None = Field(default=None, max_length=64)
    address: str | None = Field(default=None, max_length=255)
    address_number: str | None = Field(default=None, max_length=20)
    address_neighborhood: str | None = Field(default=None, max_length=120)
    address_zip: str | None = Field(default=None, max_length=10)
    address_state: str | None = Field(default=None, max_length=2)
    lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    lng: float | None = Field(default=None, ge=-180.0, le=180.0)

    @field_validator("consent")
    @classmethod
    def _consent_required(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("consent_required")
        return v


class PublicCreateMerchantOut(BaseModel):
    merchant_id: int
    trade_name: str
    status: str
    plan_code: str
    access: Literal["active", "disabled"]


class PublicMerchantAccessBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active: bool


class PublicMerchantAccessOut(BaseModel):
    merchant_id: int
    access: Literal["active", "disabled"]
    billing_status: str
