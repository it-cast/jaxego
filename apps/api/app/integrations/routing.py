"""RoutingHttpAdapter — OSRM `/route/v1` over httpx, with haversine fallback.

Contract (LOW-4 / project-osrm.org): GET `/route/v1/{profile}/{lng,lat;lng,lat}`
returns `{"code":"Ok","routes":[{"duration": <s>, "distance": <m>}, ...]}`. The
adapter NEVER raises to the caller (TH-8 / Pitfall 4): on timeout, network error,
non-Ok code, or SSRF block, it falls back to haversine ×1.4 and sets
`degraded=True`. The host allowlist + `assert_safe_url` close SSRF (TH-9 / A10).
"""

from __future__ import annotations

import structlog

from app.integrations.base import RouteResult
from app.integrations.http import assert_safe_url, build_client
from app.integrations.routing_stub import estimate_route

logger = structlog.get_logger("integrations.routing")


class RoutingHttpAdapter:
    """OSRM routing over httpx; degrades to haversine ×1.4 on any failure."""

    def __init__(self, *, base_url: str, profile: str, allowlist: set[str]) -> None:
        self._base_url = base_url.rstrip("/")
        self._profile = profile
        self._allowlist = allowlist

    async def route(self, *, origin: tuple[float, float], dest: tuple[float, float]) -> RouteResult:
        """ETA/distance via OSRM; haversine ×1.4 + degraded on any failure."""
        # OSRM coordinate order is lng,lat (not lat,lng).
        coords = f"{origin[1]},{origin[0]};{dest[1]},{dest[0]}"
        url = f"{self._base_url}/route/v1/{self._profile}/{coords}?overview=false"
        try:
            assert_safe_url(url, allowlist=self._allowlist)
            async with build_client() as client:
                resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != "Ok" or not data.get("routes"):
                raise ValueError("osrm_no_route")
            route = data["routes"][0]
            return RouteResult(
                distance_m=int(route["distance"]),
                duration_s=int(route["duration"]),
                degraded=False,
            )
        except Exception as exc:  # noqa: BLE001 — degrade, never raise (TH-8); incl. SsrfBlockedError
            # No PII to log — only the failure shape (A09).
            logger.warning("routing.degraded", error=type(exc).__name__)
            return estimate_route(origin, dest, degraded=True)
