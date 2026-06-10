"""StorageStubAdapter — dev/test only; NEVER touches B2 or the network.

Simulates the StoragePort against a temp filesystem. Presigned URLs are fake
`stub://` strings that are NOT directly fetchable — a fetch requires the key, so a
test proving "no public access without a presign" works: there is no way to read
an object except through this adapter (which the backend gates by ownership+area).

`presign_put`/`presign_get` return deterministic fake URLs; `put_bytes` writes the
file under `root`; `fetch` reads it back; reading a missing key raises KeyError
(the caller maps it to a 404 / pipeline error).
"""

from __future__ import annotations

from pathlib import Path

from app.integrations.base import PresignResult


class StorageStubAdapter:
    """Filesystem-backed StoragePort stub (no network, no real B2)."""

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # The key is server-generated (no traversal); still, resolve + verify the
        # result stays under root (defence in depth — mirrors the prod guard).
        target = (self._root / key).resolve()
        root = self._root.resolve()
        if root not in target.parents and target != root:
            raise ValueError("key escapes storage root")
        return target

    async def presign_put(self, key: str, *, content_type: str, expires_in: int) -> PresignResult:
        return PresignResult(
            url=f"stub://put/{key}?ct={content_type}&exp={expires_in}",
            method="PUT",
            expires_in=expires_in,
            headers={"Content-Type": content_type},
        )

    async def presign_get(self, key: str, *, expires_in: int) -> PresignResult:
        return PresignResult(
            url=f"stub://get/{key}?exp={expires_in}",
            method="GET",
            expires_in=expires_in,
            headers={},
        )

    async def fetch(self, key: str) -> bytes:
        path = self._path(key)
        if not path.is_file():
            raise KeyError(key)
        return path.read_bytes()

    async def put_bytes(self, key: str, data: bytes, *, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
