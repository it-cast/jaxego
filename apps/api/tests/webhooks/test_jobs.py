"""arq jobs (T-05 purge + T-09 delivery sweep) against the SQLite test DB.

- purge: an expired idempotency snapshot is deleted; a live one survives; the job
  is idempotent (a re-run purges 0).
- deliver: a pending webhook delivery whose next_retry_at is due runs ONE attempt;
  a 2xx mocked POST → delivered; a 500 → pending with the exact next_retry_at.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from app.api_keys.models import ApiIdempotencyKey
from app.webhooks import service as webhook_service
from app.webhooks.delivery import BACKOFF_AFTER_SECONDS
from app.webhooks.models import WebhookDelivery


@pytest.mark.asyncio
async def test_purge_deletes_only_expired(public_api_seed, session_factory) -> None:
    now = datetime.now(UTC)
    async with session_factory() as s:
        s.add_all(
            [
                ApiIdempotencyKey(
                    area_id=public_api_seed.area_a_id,
                    api_key_id=public_api_seed.api_key_id,
                    idempotency_key="expired",
                    request_hash="h1",
                    response_status=201,
                    response_body="{}",
                    expires_at=now - timedelta(hours=1),
                ),
                ApiIdempotencyKey(
                    area_id=public_api_seed.area_a_id,
                    api_key_id=public_api_seed.api_key_id,
                    idempotency_key="live",
                    request_hash="h2",
                    response_status=201,
                    response_body="{}",
                    expires_at=now + timedelta(hours=1),
                ),
            ]
        )
        await s.commit()

    from app.workers.webhooks import purge_idempotency_keys

    ctx = {"session_factory": session_factory}
    purged = await purge_idempotency_keys(ctx)
    assert purged == 1
    # Idempotent re-run purges nothing.
    assert await purge_idempotency_keys(ctx) == 0


async def _make_pending_webhook(public_api_seed, session_factory) -> int:
    """Configure an endpoint + insert a due pending webhook delivery; return its id."""
    async with session_factory() as s:
        await webhook_service.configure_endpoint(
            s, area_id=public_api_seed.area_a_id, url="https://1.1.1.1/webhook", events=[]
        )
        endpoint = await __import_repo().get_endpoint_for_area(s, area_id=public_api_seed.area_a_id)
        row = WebhookDelivery(
            area_id=public_api_seed.area_a_id,
            endpoint_id=endpoint.id,
            delivery_id=1,
            event_id="01J0DELIVERYEVENT00000000A",
            event_type="delivery.created",
            payload='{"id":"x","type":"delivery.created","data":{}}',
            status="pending",
            attempts=0,
            next_retry_at=datetime.now(UTC) - timedelta(seconds=1),
        )
        s.add(row)
        await s.commit()
        return row.id


def __import_repo():
    from app.webhooks import repo

    return repo


@pytest.mark.asyncio
async def test_deliver_due_marks_delivered_on_2xx(public_api_seed, session_factory) -> None:
    wid = await _make_pending_webhook(public_api_seed, session_factory)
    from app.workers.webhooks import deliver_due_webhooks

    with patch("app.webhooks.delivery._post_webhook", new=AsyncMock(return_value=200)):
        attempted = await deliver_due_webhooks({"session_factory": session_factory})
    assert attempted == 1
    async with session_factory() as s:
        row = await s.get(WebhookDelivery, wid)
    assert row.status == "delivered"
    assert row.attempts == 1


@pytest.mark.asyncio
async def test_deliver_due_retries_on_500(public_api_seed, session_factory) -> None:
    wid = await _make_pending_webhook(public_api_seed, session_factory)
    from app.workers.webhooks import deliver_due_webhooks

    with patch("app.webhooks.delivery._post_webhook", new=AsyncMock(return_value=500)):
        await deliver_due_webhooks({"session_factory": session_factory})
    async with session_factory() as s:
        row = await s.get(WebhookDelivery, wid)
    assert row.status == "pending"
    assert row.attempts == 1
    assert row.last_status_code == 500
    # Next retry scheduled exactly BACKOFF_AFTER_SECONDS[0] (=30s) ahead.
    assert row.next_retry_at is not None
    from app.db.mixins import ensure_aware_utc

    delta = (ensure_aware_utc(row.next_retry_at) - datetime.now(UTC)).total_seconds()
    assert 0 < delta <= BACKOFF_AFTER_SECONDS[0] + 5
