"""StorageB2Adapter — boto3 S3v4 against the Backblaze B2 endpoint (T-04 spike).

B2 is S3-compatible but not identical to AWS (Pitfall 1, LOW-1): it wants path-
style addressing and the region derived from the endpoint. `presign_*` are LOCAL
operations (boto3 only signs — no network), so calling the sync client from async
code is safe. Every presigned URL passes `assert_safe_url` against the B2 host
allowlist (TH-04). The internal `fetch` (download of the just-uploaded raw object
for validation) goes through the SSRF guard + `follow_redirects=False`.

The B2 application key is a SECRET sourced only from settings — never hardcoded
(Gate 8). The real impl is validated against the contracted B2 account in the
Gate 5 integration check before /gsd:verify-work; CI validates only the contract
via the Stub.
"""

from __future__ import annotations

import boto3
from botocore.config import Config

from app.integrations.base import PresignResult
from app.integrations.http import assert_safe_url, build_client


class StorageB2Adapter:
    """Async-facing StoragePort over boto3 (S3v4) against the B2 endpoint."""

    def __init__(
        self,
        *,
        endpoint_url: str,
        region: str,
        key_id: str,
        app_key: str,
        bucket: str,
        allowlist: set[str],
    ) -> None:
        self._bucket = bucket
        self._allowlist = allowlist  # B2 endpoint host(s) — SSRF allowlist (TH-04)
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=key_id,  # B2 keyID  [secret — env only]
            aws_secret_access_key=app_key,  # B2 applicationKey  [secret — env only]
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},  # B2 prefers path-style (Pitfall 1)
            ),
        )

    async def presign_put(self, key: str, *, content_type: str, expires_in: int) -> PresignResult:
        url = self._client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self._bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )
        assert_safe_url(url, allowlist=self._allowlist)  # TH-04
        return PresignResult(
            url=url,
            method="PUT",
            expires_in=expires_in,
            headers={"Content-Type": content_type},
        )

    async def presign_get(self, key: str, *, expires_in: int) -> PresignResult:
        url = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        assert_safe_url(url, allowlist=self._allowlist)  # TH-04
        return PresignResult(url=url, method="GET", expires_in=expires_in, headers={})

    async def fetch(self, key: str) -> bytes:
        """Download the raw object for server-side validation (SSRF-guarded)."""
        pres = await self.presign_get(key, expires_in=120)
        assert_safe_url(pres.url, allowlist=self._allowlist)  # re-check before connect
        async with build_client() as client:
            resp = await client.get(pres.url)
        resp.raise_for_status()
        return resp.content

    async def put_bytes(self, key: str, data: bytes, *, content_type: str) -> None:
        """Write the reprocessed derivative back to the private bucket."""
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)
