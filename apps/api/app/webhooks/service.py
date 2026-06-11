"""Webhook configuration + event enqueue (D-06/D-07/D-08).

`configure_endpoint` validates the URL anti-SSRF (T-08), generates/rotates the
signing secret, and upserts the area's single endpoint. `enqueue_event` is called
from `deliveries.service.transition` (T-07): it maps the new state to a public
event, builds the MINIMISED payload (RN-013), and inserts a `WebhookDelivery` in
`pending` with `next_retry_at=now` (the job picks it up). It is NON-BLOCKING — a
failure here NEVER derails the delivery transition (try/except at the call site).
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.webhooks import repo
from app.webhooks.models import WebhookDelivery, WebhookEndpoint
from app.webhooks.serializer import event_for_state, serialize_webhook
from app.webhooks.signing import new_event_id
from app.webhooks.ssrf import assert_safe_webhook_url

logger = structlog.get_logger("webhooks.service")


def _new_secret() -> str:
    """A fresh 256-bit webhook signing secret (shown to the area to configure)."""
    return secrets.token_urlsafe(32)


async def configure_endpoint(
    session: AsyncSession,
    *,
    area_id: int,
    url: str,
    events: list[str] | None = None,
    rotate_secret: bool = False,
    enabled: bool = True,
) -> WebhookEndpoint:
    """Upsert the area's webhook endpoint (anti-SSRF validated — T-08 / TH-05)."""
    assert_safe_webhook_url(url)
    events_str = " ".join(sorted({e.strip() for e in (events or []) if e.strip()}))

    endpoint = await repo.get_endpoint_for_area(session, area_id=area_id)
    if endpoint is None:
        endpoint = WebhookEndpoint(
            area_id=area_id,
            url=url,
            secret=_new_secret(),
            events=events_str,
            enabled=enabled,
        )
        session.add(endpoint)
    else:
        endpoint.url = url
        endpoint.events = events_str
        endpoint.enabled = enabled
        if rotate_secret:
            endpoint.secret = _new_secret()
    await session.flush()
    logger.info("webhook.endpoint_configured", area_id=area_id, endpoint_id=endpoint.id)
    return endpoint


async def enqueue_event(
    session: AsyncSession,
    *,
    area_id: int,
    delivery,
    state: str,
) -> WebhookDelivery | None:
    """Enqueue a webhook for a delivery state change (T-07). Non-blocking by contract.

    Returns the queued row, or None when there is no endpoint / the event is not
    subscribed / the endpoint is disabled. NEVER raises into the transition — the
    caller wraps this in try/except, but we also guard internally.
    """
    event_type = event_for_state(state)
    if event_type is None:
        return None

    endpoint = await repo.get_endpoint_for_area(session, area_id=area_id)
    if endpoint is None or not endpoint.enabled:
        return None
    # An empty `events` means "all"; otherwise the event must be subscribed.
    subscribed = endpoint.events.split() if endpoint.events else None
    if subscribed is not None and event_type not in subscribed:
        return None

    now = datetime.now(UTC)  # AWARE — TD-010
    event_id = new_event_id()
    payload = serialize_webhook(
        event_id=event_id,
        event_type=event_type,
        occurred_at=now.isoformat(),
        public_token=delivery.public_token,
        reference_number=delivery.reference_number,
        state=state,
        dropoff_neighborhood_id=delivery.dropoff_neighborhood_id,
        dropoff_address=delivery.dropoff_address,
        dropoff_number=delivery.dropoff_number,
        dropoff_complement=delivery.dropoff_complement,
    )
    import json

    row = WebhookDelivery(
        area_id=area_id,
        endpoint_id=endpoint.id,
        delivery_id=delivery.id,
        event_id=event_id,
        event_type=event_type,
        payload=json.dumps(payload, ensure_ascii=False),
        status="pending",
        attempts=0,
        next_retry_at=now,  # due immediately; the job picks it up
    )
    session.add(row)
    await session.flush()
    logger.info(
        "webhook.enqueued",
        area_id=area_id,
        delivery_id=delivery.id,
        event_type=event_type,
        webhook_delivery_id=row.id,
    )
    return row
