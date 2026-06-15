"""ETA fallback + circuit breaker (Phase 14 — T-03 / REQ-054 / D-04).

Exercises the routing ETA extension point:
- a live OSRM route → `source='osrm'`;
- a degraded adapter result → `source='fallback'` (never raises);
- an adapter that RAISES → still degrades to fallback (defence in depth);
- the circuit breaker OPENS after N consecutive failures and short-circuits to the
  haversine fallback WITHOUT calling OSRM;
- after the cool-off (controlled clock) the breaker half-opens and a success closes it.

A fake `RoutingPort` (no network) drives each scenario; the cool-off uses an injectable
monotonic clock so the test never sleeps.
"""

from __future__ import annotations

import pytest
from app.deliveries.eta import EtaResolver
from app.integrations.base import RouteResult

_ORIGIN = (-21.54, -42.18)
_DEST = (-21.55, -42.20)


class _FakeRouting:
    """A RoutingPort whose behaviour is scripted per call."""

    def __init__(self, *, results: list[RouteResult | Exception]) -> None:
        self._results = results
        self.calls = 0

    async def route(self, *, origin: tuple[float, float], dest: tuple[float, float]) -> RouteResult:
        self.calls += 1
        item = self._results.pop(0) if self._results else RouteResult(0, 0, degraded=True)
        if isinstance(item, Exception):
            raise item
        return item


class _Clock:
    """A controllable monotonic clock (seconds)."""

    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


@pytest.mark.asyncio
async def test_live_osrm_source() -> None:
    routing = _FakeRouting(results=[RouteResult(1200, 300, degraded=False)])
    resolver = EtaResolver(routing)
    result = await resolver.resolve(origin=_ORIGIN, dest=_DEST)
    assert result.source == "osrm"
    assert result.distance_m == 1200
    assert resolver.breaker_open is False


@pytest.mark.asyncio
async def test_degraded_falls_back() -> None:
    routing = _FakeRouting(results=[RouteResult(2000, 400, degraded=True)])
    resolver = EtaResolver(routing)
    result = await resolver.resolve(origin=_ORIGIN, dest=_DEST)
    assert result.source == "fallback"
    # The adapter's degraded numbers are passed through (haversine ×1.4 happened upstream).
    assert result.distance_m == 2000


@pytest.mark.asyncio
async def test_raising_adapter_still_falls_back() -> None:
    """Defence in depth: even if the adapter raises, ETA never blocks (D-04 / TH-08)."""
    routing = _FakeRouting(results=[TimeoutError("osrm timeout")])
    resolver = EtaResolver(routing)
    result = await resolver.resolve(origin=_ORIGIN, dest=_DEST)
    assert result.source == "fallback"
    assert result.distance_m > 0  # haversine produced a usable estimate


@pytest.mark.asyncio
async def test_breaker_opens_and_short_circuits() -> None:
    clock = _Clock()
    # 3 consecutive degraded calls open the breaker (threshold=3).
    routing = _FakeRouting(results=[RouteResult(0, 0, degraded=True) for _ in range(3)])
    resolver = EtaResolver(routing, failure_threshold=3, cooloff_seconds=30.0, clock=clock)

    for _ in range(3):
        r = await resolver.resolve(origin=_ORIGIN, dest=_DEST)
        assert r.source == "fallback"
    assert resolver.breaker_open is True
    calls_before = routing.calls

    # Breaker open → next resolve short-circuits WITHOUT calling OSRM.
    r = await resolver.resolve(origin=_ORIGIN, dest=_DEST)
    assert r.source == "fallback"
    assert routing.calls == calls_before  # no new OSRM call


@pytest.mark.asyncio
async def test_breaker_half_opens_after_cooloff_then_closes() -> None:
    clock = _Clock()
    routing = _FakeRouting(
        results=[
            RouteResult(0, 0, degraded=True),
            RouteResult(0, 0, degraded=True),
            RouteResult(0, 0, degraded=True),
            RouteResult(1500, 350, degraded=False),  # the probe succeeds
        ]
    )
    resolver = EtaResolver(routing, failure_threshold=3, cooloff_seconds=30.0, clock=clock)

    for _ in range(3):
        await resolver.resolve(origin=_ORIGIN, dest=_DEST)
    assert resolver.breaker_open is True

    # Advance past the cool-off → breaker half-opens (one probe allowed).
    clock.t = 31.0
    assert resolver.breaker_open is False
    result = await resolver.resolve(origin=_ORIGIN, dest=_DEST)
    assert result.source == "osrm"  # probe hit OSRM and succeeded
    assert resolver.breaker_open is False  # success closed it
