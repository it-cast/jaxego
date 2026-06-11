"""POST /v1/public/deliveries (T-04) — idempotency, IDOR, rate limit, validation.

Drives the real ASGI app via `auth_client` (the test SQLite session is injected).
Covers F-04: replay → same response, divergent body → 409, missing Idempotency-Key
→ 422, cross-area store → 404 (TH-03), 429 + Retry-After on flood (TH-08).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


def _headers(token: str, idem: str | None = "idem-001") -> dict[str, str]:
    h = {"Authorization": f"Bearer {token}"}
    if idem is not None:
        h["Idempotency-Key"] = idem
    return h


def _body(seed, **overrides) -> dict:
    base = {
        "merchant_external_ref": seed.merchant_external_ref,
        "pickup_address": "Rua A, 100",
        "dropoff_neighborhood_id": seed.dropoff_nbhd_id,
        "dropoff_address": "Rua B, 200",
        "recipient_name": "Maria Cliente",
        "recipient_phone_e164": "+5522988887777",
        "payment_method": "direct",
        "reference_number": "PEDIDO-42",
    }
    base.update(overrides)
    return base


@pytest.fixture(autouse=True)
def _reset_public_limiter():
    from app.api_public.router import public_create_limiter

    public_create_limiter.reset()
    yield
    public_create_limiter.reset()


@pytest.mark.asyncio
async def test_create_succeeds_and_returns_delivery(
    public_api_seed, auth_client: AsyncClient
) -> None:
    resp = await auth_client.post(
        "/v1/public/deliveries", json=_body(public_api_seed),
        headers=_headers(public_api_seed.token),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["delivery_id"] > 0
    assert data["public_token"]
    assert data["state"] == "CRIADA"


@pytest.mark.asyncio
async def test_idempotency_replay_returns_same_response(
    public_api_seed, auth_client: AsyncClient
) -> None:
    first = await auth_client.post(
        "/v1/public/deliveries", json=_body(public_api_seed),
        headers=_headers(public_api_seed.token, "same-key"),
    )
    second = await auth_client.post(
        "/v1/public/deliveries", json=_body(public_api_seed),
        headers=_headers(public_api_seed.token, "same-key"),
    )
    assert first.status_code == 201
    assert second.status_code == 201
    # SAME delivery — no second create (D-04).
    assert first.json()["delivery_id"] == second.json()["delivery_id"]
    assert first.json() == second.json()


@pytest.mark.asyncio
async def test_idempotency_same_key_different_body_is_409(
    public_api_seed, auth_client: AsyncClient
) -> None:
    await auth_client.post(
        "/v1/public/deliveries", json=_body(public_api_seed),
        headers=_headers(public_api_seed.token, "conflict-key"),
    )
    resp = await auth_client.post(
        "/v1/public/deliveries",
        json=_body(public_api_seed, recipient_name="Outro Nome"),
        headers=_headers(public_api_seed.token, "conflict-key"),
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "idempotency_key_conflict"


@pytest.mark.asyncio
async def test_missing_idempotency_key_is_422(
    public_api_seed, auth_client: AsyncClient
) -> None:
    resp = await auth_client.post(
        "/v1/public/deliveries", json=_body(public_api_seed),
        headers=_headers(public_api_seed.token, idem=None),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_missing_key_is_stable_401(public_api_seed, auth_client: AsyncClient) -> None:
    resp = await auth_client.post(
        "/v1/public/deliveries", json=_body(public_api_seed),
        headers={"Idempotency-Key": "x"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "api_key_invalid"


@pytest.mark.asyncio
async def test_cross_area_store_is_404(public_api_seed, auth_client: AsyncClient) -> None:
    # Area A's key targeting Area B's store ref → 404 (TH-03, no existence leak).
    body = _body(public_api_seed, merchant_external_ref=public_api_seed.other_merchant_external_ref)
    resp = await auth_client.post(
        "/v1/public/deliveries",
        json=body,
        headers=_headers(public_api_seed.token),
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "merchant_not_found"


@pytest.mark.asyncio
async def test_cross_area_merchant_id_is_404(
    public_api_seed, auth_client: AsyncClient
) -> None:
    resp = await auth_client.post(
        "/v1/public/deliveries",
        json=_body(
            public_api_seed, merchant_external_ref=None,
            merchant_id=public_api_seed.other_merchant_id,
        ),
        headers=_headers(public_api_seed.token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_no_store_target_is_422(public_api_seed, auth_client: AsyncClient) -> None:
    body = _body(public_api_seed, merchant_external_ref=None)
    resp = await auth_client.post(
        "/v1/public/deliveries", json=body, headers=_headers(public_api_seed.token)
    )
    assert resp.status_code == 422  # model validator: one target required


@pytest.mark.asyncio
async def test_rate_limit_returns_429_with_retry_after(
    public_api_seed, auth_client: AsyncClient
) -> None:
    from app.api_public.router import public_create_limiter

    # Exhaust the limiter for this key, then the next call is 429 + Retry-After.
    for _ in range(public_create_limiter._limit):
        public_create_limiter.check(f"api_key:{public_api_seed.api_key_id}")
    resp = await auth_client.post(
        "/v1/public/deliveries", json=_body(public_api_seed),
        headers=_headers(public_api_seed.token, "rl-key"),
    )
    assert resp.status_code == 429
    assert resp.headers.get("Retry-After") == "60"
    assert resp.json()["error"]["code"] == "rate_limited"
