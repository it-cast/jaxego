"""arq task — run the multichannel notification cascade off the request (skill push).

`notify_task(delivery_id, moment)` loads the delivery + recipient, resolves the
push/sms/email ports from the factory (Stub in dev/test), and runs `notify`. Failures
degrade silently (a notification must never crash the worker). Registered in
WorkerSettings.functions.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.deliveries.models import Delivery, Recipient
from app.integrations.factory import (
    get_email_adapter,
    get_push_adapter,
    get_sms_adapter,
)
from app.notifications.dispatcher import notify

logger = structlog.get_logger("notifications.tasks")


async def notify_task(ctx: dict[str, Any], delivery_id: int, moment: str) -> str:
    """Send the multichannel notification for a delivery moment (enqueued)."""
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        delivery = await session.get(Delivery, delivery_id)
        if delivery is None:
            return "no-delivery"
        recipient = (
            await session.get(Recipient, delivery.recipient_id)
            if delivery.recipient_id is not None
            else None
        )
        try:
            await notify(
                session,
                delivery=delivery,
                recipient=recipient,
                moment=moment,
                push=get_push_adapter(),
                sms=get_sms_adapter(),
                email=get_email_adapter(),
            )
            await session.commit()
        except Exception:  # noqa: BLE001 — a notification must not crash the worker
            logger.warning("notify_task.failed", delivery_id=delivery_id, moment=moment)
            return "failed"
    return "sent"
