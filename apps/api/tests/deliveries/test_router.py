"""HTTP path for /v1/deliveries (router + merchant_scope wiring — T-04).

Exercises the real ASGI app via `auth_client`: a logged-in store owner creates a
delivery, lists it (phone masked), reads it, cancels it; an authenticated user
with NO merchant gets 404 on the store surface (TH-03). This complements the
service-level tests by validating the dependency/serialization wiring.
"""

from __future__ import annotations

import pytest

from tests.helpers import bearer, login


def _payload(seed) -> dict:
    return {
        "pickup_address": "Rua A, 100",
        "pickup_neighborhood": "Centro",
        "dropoff_neighborhood_id": seed.dropoff_nbhd_id,
        "dropoff_address": "Rua B, 200",
        "dropoff_number": "200",
        "recipient_name": "Maria Cliente",
        "recipient_phone_e164": "+5522988887777",
        "items_description": "1 pizza",
        "items_quantity": 1,
        "proof_method": "photo",
        "payment_method": "direct",
        "distance_m": 3000,
    }


@pytest.mark.asyncio
async def test_create_list_get_cancel_flow(delivery_seed, auth_client) -> None:
    tokens = await login(auth_client, delivery_seed.owner_email, delivery_seed.password)
    headers = bearer(tokens["access_token"])

    # Create
    resp = await auth_client.post("/v1/deliveries", json=_payload(delivery_seed), headers=headers)
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["state"] == "CRIADA"
    did = created["delivery_id"]

    # List — phone masked, never raw.
    resp = await auth_client.get("/v1/deliveries", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert "+5522988887777" not in str(item)
    assert item["recipient_phone_masked"].endswith("7777")

    # Get one.
    resp = await auth_client.get(f"/v1/deliveries/{did}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["public_token"] == created["public_token"]

    # Cancel.
    resp = await auth_client.post(
        f"/v1/deliveries/{did}/cancel", json={"reason": "cliente desistiu"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["state"] == "CANCELADA"


@pytest.mark.asyncio
async def test_card_payment_returns_422(delivery_seed, auth_client) -> None:
    tokens = await login(auth_client, delivery_seed.owner_email, delivery_seed.password)
    headers = bearer(tokens["access_token"])
    payload = _payload(delivery_seed)
    payload["payment_method"] = "card"
    resp = await auth_client.post("/v1/deliveries", json=payload, headers=headers)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "payment_method_unavailable"


@pytest.mark.asyncio
async def test_other_store_delivery_404(delivery_seed, auth_client) -> None:
    # Store A creates.
    tokens_a = await login(auth_client, delivery_seed.owner_email, delivery_seed.password)
    resp = await auth_client.post(
        "/v1/deliveries", json=_payload(delivery_seed), headers=bearer(tokens_a["access_token"])
    )
    did = resp.json()["delivery_id"]

    # Store B (other merchant, other area) cannot read it → 404.
    tokens_b = await login(auth_client, delivery_seed.other_owner_email, delivery_seed.password)
    resp = await auth_client.get(f"/v1/deliveries/{did}", headers=bearer(tokens_b["access_token"]))
    assert resp.status_code == 404
