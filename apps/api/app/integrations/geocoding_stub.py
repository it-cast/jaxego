"""GeocodingStubAdapter — dev/test only; deterministic coordinates by scenario.

"padua" → a point inside the Pádua area; "fora" → a point with no covering area
(drives the "Ainda não chegamos aí" empty state); "down" → None.
"""

from __future__ import annotations

from app.integrations.base import GeocodeResult

# Approximate centroid of Santo Antônio de Pádua / RJ (pilot area).
_PADUA_POINT = GeocodeResult(lat=-21.541, lng=-42.043)
# A point far outside any seeded area (mid-Atlantic) — no coverage.
_FORA_POINT = GeocodeResult(lat=-15.0, lng=-30.0)


class GeocodingStubAdapter:
    """Configurable geocoder stub (no network)."""

    def __init__(self, scenario: str = "padua") -> None:
        self._scenario = scenario

    async def geocode(self, address: str) -> GeocodeResult | None:
        if self._scenario == "down":
            return None
        if self._scenario == "fora":
            return _FORA_POINT
        return _PADUA_POINT
