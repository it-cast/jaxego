"""Dispatch API contracts (Pydantic v2). RN-013 by construction (TH-2).

`OfferOut` is a SEPARATE schema that does NOT have the full dropoff address fields
(`dropoff_address`/`dropoff_number`/`dropoff_complement`) — it exposes ONLY the
neighborhood + distance for the destination (RN-013). It is NEVER built via
`from_attributes` over the whole Delivery model (Pitfall 2); the router constructs
it field-by-field from the allowed columns. The full destination address is
revealed only after COLETADA (Phase 9).

`ttl_total_s`/`ttl_remaining_s` come from the Redis offer (ADR-104) — the timer's
source of truth — so the app's cosmetic countdown can re-sync to the server.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class OfferOut(BaseModel):
    """The courier-facing offer. NO full dropoff address by construction (RN-013).

    Allowed destination fields: neighborhood name + distance ONLY. Origin (pickup)
    is the store's own address (revealed freely — D-04). Money is integer cents.
    """

    model_config = ConfigDict(extra="forbid")

    delivery_id: int
    loja_nome: str
    # Pickup — the store's own address (full is allowed, D-04).
    pickup_address: str
    pickup_neighborhood: str | None
    # Dropoff — RN-013: neighborhood + distance ONLY. NO street/number/complement.
    dropoff_neighborhood: str
    distance_m: int | None
    # Money (integer cents).
    value_cents: int | None
    # Payment modality (RN-023) — direct in M1.
    payment_method: str
    receipt_method: str | None = None
    # ETA (OSRM seconds) + degrade flag (haversine fallback — silent to courier).
    eta_s: int | None
    eta_degraded: bool
    # Timer — Redis TTL is the source of truth (ADR-104).
    ttl_total_s: int
    ttl_remaining_s: int


class AcceptResponse(BaseModel):
    """Result of accepting an offer — the delivery is now ACEITA (F-05)."""

    delivery_id: int
    state: str


class DeclineResponse(BaseModel):
    """Result of declining an offer — the cascade advances to the next candidate."""

    delivery_id: int
    declined: bool
