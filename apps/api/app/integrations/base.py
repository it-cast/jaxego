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
