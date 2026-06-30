"""Inngest SDK — function handler registration for FastAPI.

Registers a single function `release-scheduled-delivery` that listens for the
`delivery/scheduled-release` event and transitions the delivery from AGENDADA
to CRIADA, then enqueues the dispatch cascade.

`register_inngest(app)` is called once in `create_app()`. It mounts the Inngest
serve handler at `/api/inngest` — the URL registered in the Inngest dashboard.

The SDK reads INNGEST_SIGNING_KEY and INNGEST_EVENT_KEY directly from the
environment and auto-detects is_production from the key prefix (signkey-prod-*).
"""

from __future__ import annotations

import os

import inngest
import inngest.fast_api
import structlog

logger = structlog.get_logger("integrations.inngest_functions")

# Let the SDK read INNGEST_SIGNING_KEY from env directly — it auto-detects
# is_production from the key prefix (signkey-prod-* vs signkey-test-*).
_signing_key = os.environ.get("INNGEST_SIGNING_KEY")

_client = inngest.Inngest(
    app_id="jaxego",
    signing_key=_signing_key,
)


@_client.create_function(
    fn_id="release-scheduled-delivery",
    trigger=inngest.TriggerEvent(event="delivery/scheduled-release"),
)
async def _release_scheduled_delivery(ctx: inngest.Context) -> dict:
    """Wait until scheduled_at, then transition AGENDADA → CRIADA and start dispatch."""
    from datetime import datetime, timezone

    delivery_id: int = ctx.event.data["delivery_id"]
    scheduled_at_str: str = ctx.event.data["scheduled_at"]
    scheduled_at = datetime.fromisoformat(scheduled_at_str).astimezone(timezone.utc)

    # Aguarda até o horário agendado antes de qualquer ação.
    await ctx.step.sleep_until("wait-for-scheduled-time", scheduled_at)

    from app.db.session import async_session_factory
    from app.deliveries import service as delivery_service
    from app.workers.dispatch import enqueue_dispatch

    async with async_session_factory() as session:
        released = await delivery_service.release_scheduled_delivery(
            session, delivery_id=delivery_id
        )

    if released:
        await enqueue_dispatch(delivery_id)
        logger.info("inngest.release.dispatched", delivery_id=delivery_id)
    else:
        logger.info("inngest.release.skipped", delivery_id=delivery_id)

    return {"ok": True, "released": released}


def register_inngest(app) -> None:  # type: ignore[type-arg]
    """Mount the Inngest serve handler at /api/inngest."""
    inngest.fast_api.serve(app, _client, [_release_scheduled_delivery])
