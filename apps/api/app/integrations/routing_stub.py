"""RoutingStubAdapter — deterministic haversine routing (dev/test, no network).

Used in dev/test and as the fallback math of the real adapter. Distance is the
great-circle (haversine) distance; the road duration/distance estimate applies
the ×1.4 detour factor (RESEARCH D-08). `degraded` is False here when used as the
dev Stub (a deliberate dev choice) — the HTTP adapter sets `degraded=True` when it
falls back to this math because OSRM was unavailable.
"""

from __future__ import annotations

import math

from app.integrations.base import RouteResult

# Road detour factor over the straight-line distance (D-08).
_DETOUR = 1.4
# Average urban speed for the duration estimate (~25 km/h ≈ 6.94 m/s).
_AVG_SPEED_MS = 6.94
_EARTH_RADIUS_M = 6_371_000.0


def haversine_m(origin: tuple[float, float], dest: tuple[float, float]) -> int:
    """Great-circle distance in metres between two (lat, lng) points."""
    lat1, lng1 = origin
    lat2, lng2 = dest
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return int(_EARTH_RADIUS_M * c)


def estimate_route(
    origin: tuple[float, float], dest: tuple[float, float], *, degraded: bool
) -> RouteResult:
    """Haversine ×1.4 road estimate (shared by the Stub and the HTTP fallback)."""
    straight = haversine_m(origin, dest)
    distance_m = int(straight * _DETOUR)
    duration_s = int(distance_m / _AVG_SPEED_MS) if distance_m else 0
    return RouteResult(distance_m=distance_m, duration_s=duration_s, degraded=degraded)


class RoutingStubAdapter:
    """Deterministic haversine routing — no network (dev/test)."""

    async def route(self, *, origin: tuple[float, float], dest: tuple[float, float]) -> RouteResult:
        """Return a deterministic haversine ×1.4 estimate (degraded=False)."""
        return estimate_route(origin, dest, degraded=False)
