"""Delivery API contracts (Pydantic v2, extra='forbid' — A03 / TH-06).

`CreateDeliveryBody` is the F-03 create contract: `extra='forbid'` blocks mass
assignment, and the SERVER-DERIVED fields (`state`, `area_id`, `fee_cents`,
`courier_id`, estimates) are NOT in the body. `payment_method` is a narrow enum
accepting `direct`/`card`/`pix`, but only `direct` passes the rule (card/pix →
422 "em breve", D-02). `DeliveryOut` masks the recipient phone (TH-04). The store
surface (`DeliveryOut`) MAY carry the full dropoff address (the store owns the
data it typed); the Phase 8 courier-offer serializer must NOT (RN-013 — see
README.md).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def mask_phone_display(phone: str) -> str:
    """Mask an E.164 phone for display: keep DDI/DDD prefix + last 4.

    `+5522988887777` → `+5522 9••••-7777`. Never reveal the middle digits in the
    list/dashboard (TH-04 / LGPD). The full phone is only reachable in the
    ACEITA→FINALIZADA window (RN-022, Phases 8/9) — never while CRIADA.
    """
    if len(phone) < 8:
        return "•" * len(phone)
    return f"{phone[:5]} 9••••-{phone[-4:]}"


class PaymentMethod(str, Enum):
    """Per-delivery payment (RN-023 / D-02). Only `direct` enabled in Phase 7."""

    direct = "direct"
    card = "card"  # "em breve" (Phase 10) — accepted by the enum, rejected by the rule
    pix = "pix"  # idem


class ProofMethod(str, Enum):
    none = "none"
    photo = "photo"
    photo_reference = "photo_reference"
    otp = "otp"


class CreateDeliveryBody(BaseModel):
    """F-03 create contract. `extra='forbid'` blocks mass assignment (A03)."""

    model_config = ConfigDict(extra="forbid")

    # --- Pickup (store address — editable, pre-filled in the UI) ---
    pickup_address: str = Field(min_length=3, max_length=255)
    pickup_neighborhood: str | None = Field(default=None, max_length=120)

    # --- Dropoff (RN-013: full address persisted; neighborhood resolved in catalog) ---
    dropoff_neighborhood_id: int
    dropoff_address: str = Field(min_length=3, max_length=255)
    dropoff_number: str | None = Field(default=None, max_length=20)
    dropoff_complement: str | None = Field(default=None, max_length=120)
    dropoff_reference: str | None = Field(default=None, max_length=255)
    # CEP do endereço de entrega — usado como âncora geográfica no geocoding.
    cep: str | None = Field(default=None, max_length=9)
    # Trip distance in metres (the UI may estimate it; server uses it for km bands).
    distance_m: int | None = Field(default=None, ge=0)

    # --- Recipient (minimisation: name + phone mandatory; email/CPF optional) ---
    recipient_name: str = Field(min_length=2, max_length=120)
    recipient_phone_e164: str = Field(min_length=12, max_length=20, pattern=r"^\+\d{11,15}$")
    recipient_email: EmailStr | None = None
    # Raw CPF (digits or masked) — hashed by the service; NEVER persisted raw.
    recipient_cpf: str | None = Field(default=None, max_length=14)

    # --- Items / reference ---
    items_description: str | None = Field(default=None, max_length=500)
    items_quantity: int = Field(default=1, ge=1, le=999)
    declared_value_cents: int | None = Field(default=None, ge=0)
    # Package size/weight (MG-1) — optional. Sane upper bounds (200kg / 300cm).
    weight_g: int | None = Field(default=None, ge=0, le=200_000)
    length_cm: int | None = Field(default=None, ge=0, le=300)
    width_cm: int | None = Field(default=None, ge=0, le=300)
    height_cm: int | None = Field(default=None, ge=0, le=300)
    reference_number: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=500)

    # --- Target teams (at least one required) ---
    team_ids: list[int] = Field(min_length=1)

    # --- Choices ---
    proof_method: ProofMethod = ProofMethod.photo
    payment_method: PaymentMethod = PaymentMethod.direct
    receipt_method: str | None = Field(default=None, max_length=16)

    # --- Online payment (Phase 10 — card/pix only). card_blob is the OPAQUE RSA-OAEP
    # ciphertext from the client; the raw card NEVER arrives here (A09). ---
    card_blob: str | None = Field(default=None, max_length=4096)
    payer_document: str | None = Field(default=None, max_length=14)
    payer_email: EmailStr | None = None

    # --- Scheduled dispatch (Inngest). NULL = dispatch immediately (CRIADA). ---
    # Must be at least 5 minutes in the future (prevents near-instant scheduling
    # that would race with the immediate dispatch path).
    scheduled_at: datetime | None = Field(default=None)

    @field_validator("scheduled_at")
    @classmethod
    def scheduled_at_must_be_future(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v
        from datetime import UTC

        now = datetime.now(UTC)
        # Normalise naive datetimes to UTC (assume the client sent UTC).
        if v.tzinfo is None:
            from datetime import timezone
            v = v.replace(tzinfo=timezone.utc)
        from datetime import timedelta
        if v <= now + timedelta(minutes=1):
            raise ValueError("scheduled_at deve ser pelo menos 1 minuto no futuro.")
        return v


class DeliveryOut(BaseModel):
    """Store-facing delivery view. Recipient phone is MASKED (TH-04).

    The store owns the dropoff address it typed, so it is exposed here. The Phase 8
    courier-offer serializer must expose ONLY neighborhood + distance (RN-013).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    public_token: str
    state: str
    payment_method: str
    proof_method: str
    # Dropoff — store surface (full address allowed here; NOT in the courier offer).
    dropoff_address: str
    dropoff_number: str | None
    dropoff_complement: str | None
    dropoff_reference: str | None
    dropoff_neighborhood_id: int
    distance_m: int | None
    # Dropoff coords — store owns the address it typed; used to render the map.
    dropoff_lat: float | None = None
    dropoff_lng: float | None = None
    # Money (integer cents).
    price_cents: int | None = None
    fee_cents: int
    has_image: bool = False
    reference_number: str | None
    # Package size/weight (MG-1) — optional.
    weight_g: int | None = None
    length_cm: int | None = None
    width_cm: int | None = None
    height_cm: int | None = None
    # Recipient — name + phone (store owns the data it typed; masking applies to
    # couriers and public surfaces only — RN-022 / TH-04).
    recipient_name: str | None = None
    recipient_phone_masked: str | None = None
    recipient_phone: str | None = None
    courier_id: int | None = None
    courier_name: str | None = None
    # Extra detail fields (only populated in GET /{id}, not in list).
    items_description: str | None = None
    items_quantity: int = 1
    notes: str | None = None
    pickup_address: str | None = None
    pickup_neighborhood: str | None = None
    dropoff_neighborhood_name: str | None = None
    team_names: list[str] = []
    created_at: str | None = None
    scheduled_at: str | None = None


class DeliveryListItem(BaseModel):
    """A row of the store delivery list (screen 14). Phone masked (TH-04)."""

    id: int
    public_token: str
    state: str
    payment_method: str
    dropoff_neighborhood_id: int
    price_cents: int | None = None
    fee_cents: int
    has_image: bool = False
    reference_number: str | None
    recipient_name: str | None
    recipient_phone_masked: str | None
    courier_id: int | None
    created_at: str | None
    scheduled_at: str | None = None


class DeliveryListOut(BaseModel):
    """Paginated store delivery list (single query + COUNT — no N+1)."""

    items: list[DeliveryListItem]
    total: int
    limit: int
    offset: int


class CancelDeliveryBody(BaseModel):
    """Cancel a delivery (store, pre-acceptance). `extra='forbid'` (A03)."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=255)


class CreateDeliveryResponse(BaseModel):
    """Create result returned to the store (E2 warning surfaced here)."""

    delivery_id: int
    public_token: str
    state: str
    price_cents: int | None = None
    fee_cents: int
    has_image: bool = False
    # E2 (D-06): 0 eligible online couriers — non-blocking warning.
    no_couriers_warning: bool
    # Populated when scheduled_at was provided (AGENDADA state).
    scheduled_at: str | None = None


class CourierDeliveryOut(BaseModel):
    """A delivery as seen by the ASSIGNED courier (F1.0 / MR-1).

    PII minimisation (RN-013): the full dropoff address and the recipient are
    revealed ONLY after pickup (state COLETADA+). Before that the courier sees
    pickup (the store) + dropoff neighborhood/distance only — same contract as
    the offer. The router enforces this at serialization.
    """

    model_config = ConfigDict(extra="forbid")

    id: int
    public_token: str
    state: str
    payment_method: str
    proof_method: str
    # Store name
    merchant_trade_name: str | None = None
    # Pickup (the store) — always visible to the assigned courier.
    pickup_address: str
    pickup_neighborhood: str | None
    pickup_lat: float | None
    pickup_lng: float | None
    # Dropoff — neighborhood/distance always; full address only after pickup.
    dropoff_neighborhood_id: int
    dropoff_neighborhood_name: str | None = None
    distance_m: int | None
    dropoff_address: str | None
    dropoff_number: str | None
    dropoff_complement: str | None
    dropoff_reference: str | None
    dropoff_lat: float | None
    dropoff_lng: float | None
    # Recipient — only after pickup.
    recipient_name: str | None
    recipient_phone_masked: str | None
    recipient_phone: str | None = None
    # Money (centavos) + order metadata.
    price_cents: int | None = None
    fee_cents: int
    has_image: bool = False
    reference_number: str | None
    items_description: str | None
    items_quantity: int
    # Package size/weight (MG-1) — courier sees the size before accepting.
    weight_g: int | None
    length_cm: int | None
    width_cm: int | None
    height_cm: int | None
    courier_collection_method: str | None = None
    receipt_method: str | None = None
    notes: str | None = None
    items_description: str | None = None
    items_quantity: int = 1
    pickup_address: str | None = None
    pickup_neighborhood: str | None = None
    dropoff_neighborhood_name: str | None = None
    team_names: list[str] = []
    created_at: str | None


class CourierDeliveryListItem(BaseModel):
    """A row in the courier's delivery history (no recipient PII in the list)."""

    id: int
    public_token: str
    state: str
    payment_method: str
    pickup_address: str | None = None
    dropoff_address: str | None = None
    dropoff_number: str | None = None
    dropoff_neighborhood_id: int
    distance_m: int | None
    price_cents: int | None = None
    fee_cents: int
    has_image: bool = False
    created_at: str | None


class CourierDeliveryListOut(BaseModel):
    """Paginated courier delivery history (single query + COUNT — no N+1)."""

    items: list[CourierDeliveryListItem]
    total: int
    limit: int
    offset: int
