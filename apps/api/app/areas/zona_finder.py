"""Point-in-polygon zone finder (pure Python, no external deps).

GeoJSON Polygon coordinates are [[[lng, lat], ...]] — longitude first.
Uses the ray-casting algorithm (Jordan curve theorem).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def _point_in_polygon(lat: float, lng: float, ring: list[list[float]]) -> bool:
    """Ray-casting: ring is [[lng, lat], ...] (GeoJSON order)."""
    x, y = lng, lat
    n = len(ring)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


async def find_zona_id(
    session: AsyncSession,
    *,
    area_id: int,
    lat: float,
    lng: float,
) -> int | None:
    """Return the zona_id whose polygon contains (lat, lng), or None."""
    from app.areas.models import Zona

    zonas = list(
        (await session.execute(
            select(Zona).where(
                Zona.area_id == area_id,
                Zona.boundary.is_not(None),
            )
        )).scalars().all()
    )
    for zona in zonas:
        try:
            ring = zona.boundary["coordinates"][0]  # type: ignore[index]
            if _point_in_polygon(lat, lng, ring):
                return zona.id
        except (KeyError, TypeError, IndexError):
            continue
    return None
