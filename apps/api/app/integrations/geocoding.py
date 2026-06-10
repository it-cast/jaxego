"""GeocodingHttpAdapter — Nominatim/OSM `/search` (Discretion; default self-host).

Production impl. The base URL comes from settings and is SSRF-guarded (TH-02:
geocoding a user-supplied address is a classic SSRF vector). Redirects disabled.
A failure returns None so the caller surfaces the empty state / manual address.
"""

from __future__ import annotations

import structlog

from app.integrations.base import GeocodeResult
from app.integrations.http import SsrfBlockedError, assert_safe_url, build_client

logger = structlog.get_logger("integrations.geocoding")


class GeocodingHttpAdapter:
    """Async address geocoder (Nominatim-compatible `/search?format=json`)."""

    def __init__(self, *, base_url: str, allowlist: set[str]) -> None:
        self._base_url = base_url.rstrip("/")
        self._allowlist = allowlist

    async def geocode(self, address: str) -> GeocodeResult | None:
        url = f"{self._base_url}/search"
        try:
            assert_safe_url(url, allowlist=self._allowlist)
        except SsrfBlockedError:
            logger.error("geocoding_ssrf_blocked")
            return None
        try:
            async with build_client() as client:
                resp = await client.get(url, params={"q": address, "format": "json", "limit": 1})
            if resp.status_code != 200:
                return None
            data = resp.json()
            if not data:
                return None
            first = data[0]
            return GeocodeResult(lat=float(first["lat"]), lng=float(first["lon"]))
        except Exception:  # noqa: BLE001 — provider error -> None
            logger.warning("geocoding_provider_error")
            return None
