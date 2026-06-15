"""ETA resolution with a robust OSRM fallback (Phase 14 — T-03 / REQ-054 / D-04).

The freight ESTIMATE (price) is the median of eligible couriers (`estimate.py`) — that
path is untouched. This module is the ROUTING ETA (road distance/duration) extension
point: it wraps the `RoutingPort` (OSRM httpx adapter, which already degrades to
haversine ×1.4 on any failure) with:

  - a TIMEOUT already enforced inside the httpx adapter (`DEFAULT_TIMEOUT` — 5s); and
  - a CIRCUIT BREAKER here: after N consecutive degraded/failed calls the breaker OPENS
    and short-circuits straight to the haversine fallback for a cool-off window, so a
    sustained OSRM outage never piles up slow calls on the create-delivery path.

It NEVER raises and NEVER blocks delivery creation (D-04 / TH-08): a failure always
falls back to the haversine estimate (the same math the median path already trusts).

Observability (D-04): every resolution emits `eta_source` = `osrm` | `fallback` via
structlog, plus the breaker state on transitions. No PII is logged (only coordinates'
shape is implicit — the log carries `eta_source` and metrics, not addresses).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import structlog

from app.integrations.base import RouteResult, RoutingPort
from app.integrations.routing_stub import estimate_route

logger = structlog.get_logger("deliveries.eta")

EtaSource = Literal["osrm", "fallback"]

# Circuit breaker thresholds (D-04). Conservative: a handful of consecutive OSRM
# failures opens the breaker; it stays open for the cool-off, then probes once.
_FAILURE_THRESHOLD = 3
_COOLOFF_SECONDS = 30.0


@dataclass(frozen=True)
class EtaResult:
    """The resolved road ETA + which source produced it (D-04).

    `source='osrm'` means a live OSRM route; `source='fallback'` means the haversine
    ×1.4 estimate (OSRM degraded, timed out, or the breaker was open).
    """

    distance_m: int
    duration_s: int
    source: EtaSource


class EtaResolver:
    """Resolve a road ETA via OSRM with a circuit breaker + haversine fallback.

    Stateful (per-process): tracks consecutive failures to open/close the breaker.
    A single resolver instance is meant to be reused across requests (e.g. one per
    worker/app) so the breaker state is shared.
    """

    def __init__(
        self,
        routing: RoutingPort,
        *,
        failure_threshold: int = _FAILURE_THRESHOLD,
        cooloff_seconds: float = _COOLOFF_SECONDS,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._routing = routing
        self._failure_threshold = failure_threshold
        self._cooloff_seconds = cooloff_seconds
        # `clock` is an injectable monotonic time source (tests control cool-off).
        self._now: Callable[[], float] = clock if clock is not None else time.monotonic
        self._consecutive_failures = 0
        self._opened_at: float | None = None

    @property
    def breaker_open(self) -> bool:
        """True while the breaker is open and still within the cool-off window."""
        if self._opened_at is None:
            return False
        if self._now() - self._opened_at >= self._cooloff_seconds:
            return False  # cool-off elapsed → half-open (one probe allowed)
        return True

    def _record_success(self) -> None:
        if self._opened_at is not None:
            logger.info("eta.breaker_closed")
        self._consecutive_failures = 0
        self._opened_at = None

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._failure_threshold and self._opened_at is None:
            self._opened_at = self._now()
            logger.warning("eta.breaker_opened", consecutive_failures=self._consecutive_failures)

    async def resolve(self, *, origin: tuple[float, float], dest: tuple[float, float]) -> EtaResult:
        """Resolve the road ETA. NEVER raises; always returns a usable result (D-04)."""
        # Breaker OPEN → short-circuit to the haversine fallback (no OSRM call).
        if self.breaker_open:
            fallback = estimate_route(origin, dest, degraded=True)
            logger.info("eta.resolved", eta_source="fallback", breaker="open")
            return EtaResult(
                distance_m=fallback.distance_m,
                duration_s=fallback.duration_s,
                source="fallback",
            )

        # Breaker CLOSED or HALF-OPEN → try OSRM (the adapter never raises; it degrades).
        try:
            route: RouteResult = await self._routing.route(origin=origin, dest=dest)
        except Exception as exc:  # noqa: BLE001 — defence in depth; adapter shouldn't raise
            self._record_failure()
            logger.warning("eta.route_error", error=type(exc).__name__)
            fallback = estimate_route(origin, dest, degraded=True)
            return EtaResult(
                distance_m=fallback.distance_m,
                duration_s=fallback.duration_s,
                source="fallback",
            )

        if route.degraded:
            # OSRM was unavailable; the adapter already fell back to haversine math.
            self._record_failure()
            logger.info("eta.resolved", eta_source="fallback")
            return EtaResult(
                distance_m=route.distance_m, duration_s=route.duration_s, source="fallback"
            )

        # Live OSRM route — success closes/resets the breaker.
        self._record_success()
        logger.info("eta.resolved", eta_source="osrm")
        return EtaResult(distance_m=route.distance_m, duration_s=route.duration_s, source="osrm")
