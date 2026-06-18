"""StorageStubAdapter — dev/test only; NEVER touches B2 or the network.

Simulates the StoragePort against a temp filesystem. In dev mode, presigned
URLs point to `http://localhost:8000/v1/dev/upload/{key}` so the frontend can
PUT files normally. In test mode (base_url=None), URLs use the `stub://` scheme
that is NOT fetchable (tests verifying "no public access" still work).

`put_bytes` writes the file under `root`; `fetch` reads it back; reading a
missing key raises KeyError (the caller maps it to a 404 / pipeline error).
"""

from __future__ import annotations

from pathlib import Path

from app.integrations.base import PresignResult


class StorageStubAdapter:
    """Filesystem-backed StoragePort stub (no network, no real B2)."""

    def __init__(self, root: Path | str, *, base_url: str | None = None) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._base_url = base_url

    def _path(self, key: str) -> Path:
        # The key is server-generated (no traversal); still, resolve + verify the
        # result stays under root (defence in depth — mirrors the prod guard).
        target = (self._root / key).resolve()
        root = self._root.resolve()
        if root not in target.parents and target != root:
            raise ValueError("key escapes storage root")
        return target

    async def presign_put(self, key: str, *, content_type: str, expires_in: int) -> PresignResult:
        if self._base_url:
            url = f"/v1/upload/{key}"
        else:
            url = f"stub://put/{key}?ct={content_type}&exp={expires_in}"
        return PresignResult(
            url=url,
            method="PUT",
            expires_in=expires_in,
            headers={"Content-Type": content_type},
        )

    async def presign_get(self, key: str, *, expires_in: int) -> PresignResult:
        if self._base_url:
            url = f"/v1/upload/{key}"
        else:
            url = f"stub://get/{key}?exp={expires_in}"
        return PresignResult(
            url=url,
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
