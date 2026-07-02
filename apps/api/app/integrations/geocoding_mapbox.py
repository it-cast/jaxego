"""MapboxGeocodingAdapter — Mapbox Geocoding API v5.

Endpoint: /geocoding/v5/mapbox.places/{query}.json
Response: GeoJSON FeatureCollection; coordinates are [lng, lat] in feature.center.
Restricted to Brazil (country=BR) for precision. Returns None on any failure so
the caller can handle the empty state gracefully.
"""

from __future__ import annotations

import urllib.parse

import structlog

from app.integrations.base import GeocodeResult
from app.integrations.http import SsrfBlockedError, assert_safe_url, build_client

logger = structlog.get_logger("integrations.geocoding_mapbox")

_MAPBOX_HOST = "api.mapbox.com"
_BASE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"


class MapboxGeocodingAdapter:
    """Async address geocoder using the Mapbox Geocoding API v5."""

    def __init__(self, *, token: str) -> None:
        self._token = token

    async def geocode(self, address: str) -> GeocodeResult | None:
        encoded = urllib.parse.quote(address, safe="")
        url = f"{_BASE_URL}/{encoded}.json"
        try:
            assert_safe_url(url, allowlist={_MAPBOX_HOST})
        except SsrfBlockedError:
            logger.error("geocoding_mapbox_ssrf_blocked", url=url)
            return None
        try:
            async with build_client() as client:
                resp = await client.get(
                    url,
                    params={
                        "access_token": self._token,
                        "limit": 1,
                        "country": "BR",
                        "language": "pt",
                    },
                )
            if resp.status_code != 200:
                logger.warning("geocoding_mapbox_error", status=resp.status_code)
                return None
            features = resp.json().get("features", [])
            if not features:
                return None
            lng, lat = features[0]["center"]
            return GeocodeResult(lat=lat, lng=lng)
        except Exception:  # noqa: BLE001
            logger.warning("geocoding_mapbox_provider_error")
            return None
