"""Server-side geofence — distance ≤ radius from a target POINT (RN-005 / TH-1).

The proof GPS (EXIF or client `{lat,lng}`) is EVIDENCE, never authority: the
barrier is this server-side check, not the origin of the coordinate. `within_radius`
asks MySQL `ST_Distance_Sphere(POINT(lng,lat), POINT(lng,lat))` (metres, SRID 4326,
`POINT(x,y)` = `POINT(longitude, latitude)` — Pitfall 4) whether the proof point is
inside `radius_m` of the pickup/dropoff POINT (`deliveries.pickup_lat/lng` or
`dropoff_lat/lng`, confirmed present in models.py). `radius_m = AreaConfig.geofence_m`
(30..300, default 80 — Phase 6).

`haversine_m` is the documented Python fallback (A1) used when the spatial query is
unavailable; it is also unit-tested in isolation so the geofence has a deterministic,
DB-free reference. The query is fully parametrised (`:plat/:plng/...`) — no string
interpolation of coordinates (A03 anti-injection).
"""

from __future__ import annotations

import math

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Mean Earth radius in metres (WGS84 spherical approximation) — matches the sphere
# model ST_Distance_Sphere uses, so the fallback agrees with the DB within metres.
_EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres between two lat/lng points (A1 fallback).

    Pure Python, no DB. Used when the spatial query is unavailable and as the
    DB-free reference in tests. Order is (lat, lng) for both points — the lng/lat
    axis swap that bites ST_Distance_Sphere (Pitfall 4) does not apply here.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))


async def distance_m(
    session: AsyncSession,
    *,
    lat: float,
    lng: float,
    target_lat: float,
    target_lng: float,
) -> float:
    """Metres between the proof point and the target via ST_Distance_Sphere.

    `POINT(:lng, :lat)` — MySQL `POINT(x, y)` is `POINT(longitude, latitude)`
    (Pitfall 4). Parametrised (anti-injection — A03). If the dialect has no spatial
    function (SQLite dev), falls back to `haversine_m` so the call never raises.
    """
    if session.bind is not None and session.bind.dialect.name != "mysql":
        # SQLite (dev/test) has no ST_Distance_Sphere — use the documented fallback.
        return haversine_m(lat, lng, target_lat, target_lng)
    row = await session.execute(
        text("SELECT ST_Distance_Sphere(POINT(:plng, :plat), POINT(:tlng, :tlat)) AS d"),
        {"plng": lng, "plat": lat, "tlng": target_lng, "tlat": target_lat},
    )
    return float(row.scalar_one())


async def within_radius(
    session: AsyncSession,
    *,
    lat: float,
    lng: float,
    target_lat: float,
    target_lng: float,
    radius_m: int,
) -> bool:
    """True if the proof point is within `radius_m` of the target (RN-005 / TH-1)."""
    return (
        await distance_m(session, lat=lat, lng=lng, target_lat=target_lat, target_lng=target_lng)
        <= radius_m
    )
