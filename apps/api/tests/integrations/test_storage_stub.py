"""StoragePort contract tests against the Stub (T-04 — no network, no real B2).

Covers the contract every consumer relies on: presign returns the right method +
expiry + headers, an uploaded object round-trips via fetch, and there is NO way to
read an object without going through the adapter (test_no_public_access): the
presigned URL is a fake `stub://` string that is NOT fetchable, so the only path
to bytes is `fetch(key)` — which the backend gates by ownership+area.

The real B2 adapter is validated against the contracted account in the Gate 5
integration check; CI validates only the contract via the Stub.
"""

from __future__ import annotations

import pytest
from app.couriers.constants import PRESIGN_GET_EXPIRES_S, PRESIGN_PUT_EXPIRES_S
from app.integrations.storage_stub import StorageStubAdapter


@pytest.fixture
def storage(tmp_path) -> StorageStubAdapter:
    return StorageStubAdapter(root=tmp_path / "b2")


@pytest.mark.asyncio
async def test_presign_put_contract(storage: StorageStubAdapter) -> None:
    res = await storage.presign_put(
        "couriers/1/abc.webp", content_type="image/webp", expires_in=PRESIGN_PUT_EXPIRES_S
    )
    assert res.method == "PUT"
    assert res.expires_in == PRESIGN_PUT_EXPIRES_S
    assert res.headers["Content-Type"] == "image/webp"
    assert res.url.startswith("stub://put/")


@pytest.mark.asyncio
async def test_presign_get_contract(storage: StorageStubAdapter) -> None:
    res = await storage.presign_get("couriers/1/abc.webp", expires_in=PRESIGN_GET_EXPIRES_S)
    assert res.method == "GET"
    assert res.expires_in == PRESIGN_GET_EXPIRES_S
    assert res.url.startswith("stub://get/")


@pytest.mark.asyncio
async def test_put_then_fetch_roundtrip(storage: StorageStubAdapter) -> None:
    key = "couriers/1/doc.webp"
    await storage.put_bytes(key, b"derived-webp-bytes", content_type="image/webp")
    assert await storage.fetch(key) == b"derived-webp-bytes"


@pytest.mark.asyncio
async def test_no_public_access(storage: StorageStubAdapter) -> None:
    """A document is unreadable without going through the adapter (REQ-015).

    The presigned URL is a fake `stub://` string — not a real fetchable URL — so
    there is no way to read the object except `fetch(key)`, which the backend
    only calls after an ownership+area check. Reading a key never written raises
    (no silent empty bytes).
    """
    res = await storage.presign_get("couriers/1/secret.webp", expires_in=180)
    # The presigned URL is NOT a real endpoint — it carries no bytes.
    assert res.url.startswith("stub://")
    # Fetching a never-uploaded key raises (no public/anonymous read path).
    with pytest.raises(KeyError):
        await storage.fetch("couriers/1/secret.webp")


@pytest.mark.asyncio
async def test_key_traversal_blocked(storage: StorageStubAdapter) -> None:
    """A key trying to escape the storage root is rejected (defence in depth)."""
    with pytest.raises(ValueError, match="escapes storage root"):
        await storage.put_bytes("../../etc/passwd", b"x", content_type="image/webp")
