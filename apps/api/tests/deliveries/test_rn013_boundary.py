"""RN-013 structural boundary (T-05): dropoff address fields are SEPARATED.

The store surface (`DeliveryOut`) MAY carry the full dropoff address (the store
owns it). The model separates the FULL-address fields (revealed after pickup,
Phase 9) from the OFFER fields (revealed before pickup, Phase 8) so the Phase 8
offer serializer can be built without the full address BY CONSTRUCTION. This test
locks that separation so a future refactor cannot silently merge them.
"""

from __future__ import annotations

from app.deliveries.models import Delivery
from app.deliveries.schemas import DeliveryOut

# Fields revealed ONLY after pickup (Phase 9) — must NOT enter the Phase 8 offer.
FULL_ADDRESS_FIELDS = {"dropoff_address", "dropoff_number", "dropoff_complement"}
# Fields revealed BEFORE pickup (the Phase 8 offer).
OFFER_FIELDS = {"dropoff_neighborhood_id", "distance_m"}


def test_model_separates_full_address_from_offer_fields() -> None:
    columns = set(Delivery.__table__.columns.keys())
    assert FULL_ADDRESS_FIELDS <= columns
    assert OFFER_FIELDS <= columns
    # The two sets are disjoint — the separation is real, not an alias.
    assert FULL_ADDRESS_FIELDS.isdisjoint(OFFER_FIELDS)


def test_store_deliveryout_exposes_full_address() -> None:
    fields = set(DeliveryOut.model_fields.keys())
    # The store owns its typed address, so it IS exposed on the store surface.
    assert FULL_ADDRESS_FIELDS <= fields
    assert OFFER_FIELDS <= fields


def test_deliveryout_masks_recipient_phone_field_name() -> None:
    # The output carries a MASKED phone field, never a raw `recipient_phone_e164`.
    fields = set(DeliveryOut.model_fields.keys())
    assert "recipient_phone_masked" in fields
    assert "recipient_phone_e164" not in fields
