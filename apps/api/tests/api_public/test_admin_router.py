"""Admin router (T-10) — area-admin manages keys + webhook (RBAC + IDOR + secret-once).

Drives the ASGI app with a real area-admin JWT. Covers: create returns the secret
ONCE (D-01); the list never carries the secret (TH-09); a cross-area admin reaching
another area's `area_id` is 403 (A01); revoke flips the row; webhook config rejects
an unsafe URL (T-08) and accepts a public https URL.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


def _bearer(jwt: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {jwt}"}


@pytest.mark.asyncio
async def test_create_key_returns_secret_once(public_api_seed, auth_client: AsyncClient) -> None:
    resp = await auth_client.post(
        f"/v1/admin/areas/{public_api_seed.area_a_id}/api-keys",
        json={"name": "Integração X", "scopes": ["deliveries:write"]},
        headers=_bearer(public_api_seed.admin_a_jwt),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["secret"].startswith(f"jxg_{data['key_id']}_")


@pytest.mark.asyncio
async def test_list_never_leaks_secret(public_api_seed, auth_client: AsyncClient) -> None:
    resp = await auth_client.get(
        f"/v1/admin/areas/{public_api_seed.area_a_id}/api-keys",
        headers=_bearer(public_api_seed.admin_a_jwt),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    for item in body["items"]:
        assert "secret" not in item
        assert "secret_hash" not in item


@pytest.mark.asyncio
async def test_cross_area_admin_is_403(public_api_seed, auth_client: AsyncClient) -> None:
    # Area B admin trying to manage Area A keys → 403 (A01).
    resp = await auth_client.get(
        f"/v1/admin/areas/{public_api_seed.area_a_id}/api-keys",
        headers=_bearer(public_api_seed.admin_b_jwt),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_revoke_key_flips_status(public_api_seed, auth_client: AsyncClient) -> None:
    created = await auth_client.post(
        f"/v1/admin/areas/{public_api_seed.area_a_id}/api-keys",
        json={"name": "To Revoke", "scopes": ["deliveries:write"]},
        headers=_bearer(public_api_seed.admin_a_jwt),
    )
    key_pk = created.json()["id"]
    resp = await auth_client.delete(
        f"/v1/admin/areas/{public_api_seed.area_a_id}/api-keys/{key_pk}",
        headers=_bearer(public_api_seed.admin_a_jwt),
    )
    assert resp.status_code == 200
    assert resp.json()["revoked"] is True


@pytest.mark.asyncio
async def test_configure_webhook_rejects_unsafe_url(
    public_api_seed, auth_client: AsyncClient
) -> None:
    resp = await auth_client.put(
        f"/v1/admin/areas/{public_api_seed.area_a_id}/webhook",
        json={"url": "http://169.254.169.254/meta", "events": []},
        headers=_bearer(public_api_seed.admin_a_jwt),
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "webhook_url_invalid"


@pytest.mark.asyncio
async def test_configure_webhook_accepts_public_https(
    public_api_seed, auth_client: AsyncClient
) -> None:
    resp = await auth_client.put(
        f"/v1/admin/areas/{public_api_seed.area_a_id}/webhook",
        json={"url": "https://1.1.1.1/webhook", "events": ["delivery.created"]},
        headers=_bearer(public_api_seed.admin_a_jwt),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["url"] == "https://1.1.1.1/webhook"
    assert data["secret"]  # the area's own signing secret is returned


@pytest.mark.asyncio
async def test_webhook_deliveries_history_empty_initially(
    public_api_seed, auth_client: AsyncClient
) -> None:
    resp = await auth_client.get(
        f"/v1/admin/areas/{public_api_seed.area_a_id}/webhook/deliveries",
        headers=_bearer(public_api_seed.admin_a_jwt),
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
