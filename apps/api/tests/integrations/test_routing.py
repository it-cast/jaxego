"""Routing adapter (REQ-054 / D-08): Stub haversine + the degraded fallback.

The Stub returns a deterministic haversine ×1.4 estimate (no network). The HTTP
adapter, pointed at an unreachable/blocked host, MUST degrade to haversine and set
`eta_degraded` WITHOUT raising (TH-8 / Pitfall 4) — the cascade never blocks.
"""

from __future__ import annotations

import pytest
from app.integrations.routing import RoutingHttpAdapter
from app.integrations.routing_stub import RoutingStubAdapter, haversine_m

# Pádua-ish coordinates (lat, lng).
_ORIGIN = (-21.5408, -42.1786)
_DEST = (-21.5500, -42.1700)


async def test_stub_is_deterministic_haversine() -> None:
    adapter = RoutingStubAdapter()
    r1 = await adapter.route(origin=_ORIGIN, dest=_DEST)
    r2 = await adapter.route(origin=_ORIGIN, dest=_DEST)
    assert r1 == r2  # deterministic
    assert r1.degraded is False
    # The road estimate is the straight line ×1.4 (the detour factor).
    straight = haversine_m(_ORIGIN, _DEST)
    assert r1.distance_m == int(straight * 1.4)
    assert r1.duration_s > 0


async def test_http_adapter_degrades_on_ssrf_block() -> None:
    """A host NOT in the allowlist trips the SSRF guard → degrade, never raise."""
    adapter = RoutingHttpAdapter(
        base_url="http://169.254.169.254",  # metadata IP — never allowlisted
        profile="driving",
        allowlist={"router.project-osrm.org"},
    )
    result = await adapter.route(origin=_ORIGIN, dest=_DEST)
    assert result.degraded is True  # eta_degraded flag set
    assert result.distance_m > 0  # haversine fallback still gives a value
    assert result.duration_s > 0


async def test_http_adapter_degrades_on_network_error() -> None:
    """An unreachable allowlisted host degrades silently (no exception)."""
    adapter = RoutingHttpAdapter(
        base_url="https://router.project-osrm.invalid",
        profile="driving",
        allowlist={"router.project-osrm.invalid"},
    )
    result = await adapter.route(origin=_ORIGIN, dest=_DEST)
    assert result.degraded is True


@pytest.mark.parametrize("distance", [0, 500, 5000])
async def test_zero_and_short_distances(distance: int) -> None:
    """Degenerate inputs do not crash the haversine math."""
    adapter = RoutingStubAdapter()
    # Same point → zero distance.
    result = await adapter.route(origin=_ORIGIN, dest=_ORIGIN)
    assert result.distance_m == 0
    assert result.duration_s == 0
