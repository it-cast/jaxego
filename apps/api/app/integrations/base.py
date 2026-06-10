"""Adapter Protocols + result dataclasses for the four external integrations.

Pattern 1 (RESEARCH): a `typing.Protocol` per integration, an httpx impl and a
Stub. The service depends on the Protocol, never on a concrete impl, so the test
suite injects a Stub (no network).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


# ---------------------------------------------------------------------------
# Receita Federal (CNPJ validation)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ReceitaResult:
    """Outcome of a CNPJ lookup. `situacao` ∈ {ativa, inativa, inexistente}."""

    situacao: str
    razao_social: str | None = None
    cnaes: list[str] = field(default_factory=list)


class ReceitaPort(Protocol):
    """CNPJ validation. Returns None when the provider is UNAVAILABLE (E4)."""

    async def consultar_cnpj(self, cnpj: str) -> ReceitaResult | None: ...


# ---------------------------------------------------------------------------
# SMS (OTP delivery)
# ---------------------------------------------------------------------------
class SmsPort(Protocol):
    """Send an OTP code to an E.164 phone. Returns True if accepted by provider."""

    async def send_otp(self, phone_e164: str, code: str) -> bool: ...


# ---------------------------------------------------------------------------
# E-mail (SES — confirmation link)
# ---------------------------------------------------------------------------
class EmailPort(Protocol):
    """Send an e-mail confirmation link. Returns True if accepted."""

    async def send_confirm_link(self, email: str, token: str) -> bool: ...


# ---------------------------------------------------------------------------
# Geocoding (address -> point -> area resolution)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GeocodeResult:
    """Resolved coordinates for an address."""

    lat: float
    lng: float


class GeocodingPort(Protocol):
    """Resolve an address to a point. Returns None when geocoding fails."""

    async def geocode(self, address: str) -> GeocodeResult | None: ...


# ---------------------------------------------------------------------------
# Object storage (Backblaze B2, S3-compatible) — KYC documents, PRIVATE bucket.
# Bytes NEVER transit the backend on upload (presigned PUT direct to B2). The
# StoragePort is shared (Phase 9 proofs reuse the same contract).
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PresignResult:
    """A presigned URL the client (PUT) or admin (GET) uses directly.

    `headers` are the headers the caller MUST send with the request (e.g. the
    Content-Type bound into the PUT signature).
    """

    url: str
    method: str  # "PUT" | "GET"
    expires_in: int  # seconds
    headers: dict[str, str]


class StoragePort(Protocol):
    """Private object storage (B2 S3-compatible).

    `presign_put` / `presign_get` are LOCAL operations (no network — boto3 just
    signs). `fetch` downloads the raw object for server-side validation;
    `put_bytes` writes the reprocessed derivative back.
    """

    async def presign_put(
        self, key: str, *, content_type: str, expires_in: int
    ) -> PresignResult: ...
    async def presign_get(self, key: str, *, expires_in: int) -> PresignResult: ...
    async def fetch(self, key: str) -> bytes: ...
    async def put_bytes(self, key: str, data: bytes, *, content_type: str) -> None: ...
