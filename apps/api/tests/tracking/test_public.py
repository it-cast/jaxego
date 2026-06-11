"""GET /v1/public/tracking/{token} — no auth, 404 genérico, minimised payload (TH-3).

The endpoint uses the test session via `auth_client` (which overrides get_session)
but is called WITHOUT any Authorization header — it is a public route. An unknown
token → 404 with the generic envelope (anti-enumeração). A valid token returns the
minimised payload; courier PII never appears in the response body.
"""

from __future__ import annotations

import pytest

from tests.tracking.conftest import MakeDelivery


@pytest.mark.asyncio
async def test_invalid_token_returns_generic_404(auth_client) -> None:
    resp = await auth_client.get("/v1/public/tracking/NOPENOPENOPENOPENOPENOPE00")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "not_found"
    # Generic message — never reveals whether a token exists.
    assert "não encontrado" in body["error"]["message"].lower()


@pytest.mark.asyncio
async def test_valid_token_no_auth_returns_payload(
    auth_client, make_delivery: MakeDelivery
) -> None:
    delivery = await make_delivery(state="COLETADA", public_token="PUBTOKENCOLETADA0000000001")
    # No Authorization header — public.
    resp = await auth_client.get(f"/v1/public/tracking/{delivery.public_token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "COLETADA"
    assert isinstance(data["timeline"], list)
    # Courier PII must not appear anywhere in the body.
    blob = resp.text.lower()
    assert "+5522" not in blob  # courier phone
    assert "joão entregador" not in blob  # courier name
    # vehicle type is allowed
    assert data["courier"] == {"vehicle_type": "moto"}


@pytest.mark.asyncio
async def test_address_hidden_before_coletada_via_endpoint(
    auth_client, make_delivery: MakeDelivery
) -> None:
    delivery = await make_delivery(state="ACEITA", public_token="PUBTOKENACEITA000000000001")
    resp = await auth_client.get(f"/v1/public/tracking/{delivery.public_token}")
    assert resp.status_code == 200
    assert "Rua das Flores" not in resp.text
    assert resp.json()["dropoff"] == {"neighborhood_id": delivery.dropoff_neighborhood_id}


@pytest.mark.asyncio
async def test_position_exposed_while_moving(auth_client, make_delivery: MakeDelivery) -> None:
    delivery = await make_delivery(
        state="COLETADA", public_token="PUBTOKENMOVING0000000000001", with_location=True
    )
    resp = await auth_client.get(f"/v1/public/tracking/{delivery.public_token}")
    pos = resp.json()["courier_position"]
    assert pos is not None
    # Approximate (rounded), never the precise sample.
    assert pos["lat"] == round(-21.5405, 3)
