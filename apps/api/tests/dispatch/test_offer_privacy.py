"""Offer privacy contract (REQ-025 / RN-013 / TH-2).

The `OfferOut` payload must NOT contain the full dropoff address — only the
neighborhood + distance. Asserted at the schema field level AND on a built offer.
"""

from __future__ import annotations

from app.dispatch import offer_state
from app.dispatch.schemas import OfferOut
from app.dispatch.service import build_offer_view

from tests.dispatch.conftest import DispatchSeed


def test_offer_schema_has_no_full_address_fields() -> None:
    """RN-013 by construction: the schema simply does not have the FULL fields."""
    fields = set(OfferOut.model_fields.keys())
    assert "dropoff_address" not in fields
    assert "dropoff_number" not in fields
    assert "dropoff_complement" not in fields
    # The allowed destination fields ARE present.
    assert "dropoff_neighborhood" in fields
    assert "distance_m" in fields


async def test_built_offer_payload_excludes_full_address(
    dispatch_seed: DispatchSeed, session_factory, fake_redis
) -> None:
    seed = dispatch_seed
    await offer_state.open_offer(
        fake_redis,
        delivery_id=seed.delivery_id,
        courier_id=seed.favorite_courier_id,
        timeout_s=20,
    )
    from app.deliveries.models import Delivery

    async with session_factory() as s:
        delivery = await s.get(Delivery, seed.delivery_id)
        assert delivery is not None
        offer = await build_offer_view(s, fake_redis, delivery=delivery)

    payload = offer.model_dump()
    # The exact RN-013 contract assertion.
    assert "dropoff_address" not in payload
    assert "dropoff_number" not in payload
    assert "dropoff_complement" not in payload
    # The secret street must not leak through ANY field value either.
    assert "Rua Secreta" not in str(payload)
    assert "999" != str(payload.get("dropoff_neighborhood"))
    # Allowed: neighborhood name + distance.
    assert payload["dropoff_neighborhood"] == "Vila Nova"
    assert payload["distance_m"] == 2800
    # Timer comes from Redis (ADR-104).
    assert payload["ttl_total_s"] == 20
    assert payload["ttl_remaining_s"] > 0
