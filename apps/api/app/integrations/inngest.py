"""Inngest client — schedule delivery dispatch at a future time.

`InngestClient` (real): sends an event to the Inngest API with a future `ts`
field. Inngest fires the registered function at that time, which calls back
`POST /v1/deliveries/scheduled/release`.

`InngestClientStub` (dev/test): logs instead of calling the network; returns a
deterministic fake event ID so the integration can be tested without credentials.

`get_inngest_client()` returns the real client when `inngest_event_key` is set in
settings; falls back to the stub otherwise (same factory pattern as the other
adapters in this package).

Security: the signing key (settings.inngest_signing_key) is used in the router to
verify the `x-inngest-signature` header on incoming webhook calls — it is NOT used
here (this module only sends events, never receives them).
"""

from __future__ import annotations

from datetime import datetime

import structlog

logger = structlog.get_logger("integrations.inngest")

# Event name the Inngest function listens for.
_EVENT_NAME = "delivery/scheduled-release"


class InngestClient:
    """Real Inngest client — sends events via the Inngest REST API."""

    def __init__(self, *, event_key: str, api_url: str) -> None:
        self._event_key = event_key
        self._api_url = api_url.rstrip("/")

    async def schedule(self, delivery_id: int, run_at: datetime) -> str | None:
        """Send a scheduled event to Inngest; returns the event ID or None on error.

        The `ts` field (Unix ms) tells Inngest when to fire the function. A failure
        here is best-effort — the delivery is already persisted as AGENDADA and ops
        can manually re-trigger or the store can re-schedule.
        """
        import httpx

        payload = {
            "name": _EVENT_NAME,
            # scheduled_at (ISO-8601 UTC) é lido pelo step.sleep_until() na função.
            "data": {"delivery_id": delivery_id, "scheduled_at": run_at.isoformat()},
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{self._api_url}/e/{self._event_key}",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                ids = data.get("ids") or []
                event_id: str | None = ids[0] if ids else None
                logger.info(
                    "inngest.schedule.ok",
                    delivery_id=delivery_id,
                    event_id=event_id,
                    run_at=run_at.isoformat(),
                )
                return event_id
        except Exception:  # noqa: BLE001 — best-effort; never block delivery creation
            logger.warning("inngest.schedule.failed", delivery_id=delivery_id)
            return None


class InngestClientStub:
    """Dev/test stub — logs and returns a fake event ID (no network)."""

    async def schedule(self, delivery_id: int, run_at: datetime) -> str | None:
        fake_id = f"stub-evt-{delivery_id}-{int(run_at.timestamp())}"
        logger.info(
            "inngest.stub.schedule",
            delivery_id=delivery_id,
            event_id=fake_id,
            run_at=run_at.isoformat(),
        )
        return fake_id


def get_inngest_client() -> InngestClient | InngestClientStub:
    from app.core.config import get_settings

    s = get_settings()
    if s.inngest_event_key:
        return InngestClient(event_key=s.inngest_event_key, api_url=s.inngest_api_url)
    return InngestClientStub()
