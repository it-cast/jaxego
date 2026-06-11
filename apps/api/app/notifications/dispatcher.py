"""Multichannel notification dispatcher (RN-018 / RN-031 / REQ-049).

Three moments, each enqueued on arq (never synchronous in the request — skill push):
  - accepted  → push → email   (fallback push→email)
  - on_the_way → push + SMS + email  (SMS ONLY here — quota RN-018; link de tracking)
  - delivered → push → email

`notify` records EVERY attempt in `notifications` (channel + status, no PII — A09/TH-8)
and applies the fallback: if push fails, email; for on_the_way, SMS is attempted in
addition (the "a caminho" link), and if SMS fails the email still carries the link.
The push payload is `PushMessage` (delivery_id + deep link + title — zero PII, LOW-5).

`enqueue_notification` puts a `notify_task` on the queue; `notify_task` (registered in
WorkerSettings) loads the ports from the factory and runs `notify`. Best-effort: a
queue hiccup must never break the request that triggered the notification.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deliveries.models import Delivery, Recipient
from app.integrations.base import EmailPort, PushMessage, PushPort, SmsPort
from app.notifications.models import Notification, PushSubscription

logger = structlog.get_logger("notifications.dispatcher")

# SMS is sent ONLY at the on_the_way moment (RN-018 quota).
_SMS_MOMENT = "on_the_way"


def _tracking_link(delivery: Delivery) -> str:
    """The public tracking deep link (token only — no PII, TH-9)."""
    return f"/r/{delivery.public_token}"


async def _record(
    session: AsyncSession, *, delivery: Delivery, moment: str, channel: str, status: str
) -> None:
    """Append a channel attempt to `notifications` (no PII — A09).

    `status` ∈ {sent, failed, skipped}.
    """
    session.add(
        Notification(
            area_id=delivery.area_id,
            delivery_id=delivery.id,
            moment=moment,
            channel=channel,
            status=status,
            created_at=datetime.now(UTC),  # AWARE — TD-010
        )
    )


async def _push_subscriptions(session: AsyncSession, delivery_id: int) -> list[PushSubscription]:
    stmt = select(PushSubscription).where(PushSubscription.delivery_id == delivery_id)
    return list((await session.execute(stmt)).scalars().all())


async def _try_push(
    session: AsyncSession, push: PushPort, *, delivery: Delivery, moment: str, title: str
) -> bool:
    """Send a push to each registered device; True if ANY succeeded."""
    subs = await _push_subscriptions(session, delivery.id)
    if not subs:
        await _record(session, delivery=delivery, moment=moment, channel="push", status="skipped")
        return False
    any_ok = False
    for sub in subs:
        msg = PushMessage(
            subscription=json.loads(sub.keys_json),
            delivery_id=delivery.id,
            deep_link=_tracking_link(delivery),
            title=title,
        )
        ok = await push.send(msg)
        any_ok = any_ok or ok
    await _record(
        session,
        delivery=delivery,
        moment=moment,
        channel="push",
        status="sent" if any_ok else "failed",
    )
    return any_ok


async def notify(
    session: AsyncSession,
    *,
    delivery: Delivery,
    recipient: Recipient | None,
    moment: str,
    push: PushPort,
    sms: SmsPort,
    email: EmailPort,
) -> None:
    """Run the multichannel cascade for a delivery moment (RN-018 fallback)."""
    title = {
        "accepted": "Pedido aceito",
        "on_the_way": "Seu pedido está a caminho",
        "delivered": "Pedido entregue",
    }.get(moment, "Atualização do pedido")

    push_ok = await _try_push(session, push, delivery=delivery, moment=moment, title=title)

    # on_the_way: SMS too (ONLY here — RN-018 quota), carrying the tracking link.
    sms_ok = False
    if moment == _SMS_MOMENT and recipient is not None:
        sms_ok = await sms.send_otp(recipient.phone_e164, _tracking_link(delivery))
        await _record(
            session,
            delivery=delivery,
            moment=moment,
            channel="sms",
            status="sent" if sms_ok else "failed",
        )

    # Email fallback: when push did NOT reach (RN-018 push→email). For on_the_way the
    # email is also the SMS fallback (still carries the link).
    if not push_ok and recipient is not None and recipient.email:
        email_ok = await email.send_confirm_link(recipient.email, _tracking_link(delivery))
        await _record(
            session,
            delivery=delivery,
            moment=moment,
            channel="email",
            status="sent" if email_ok else "failed",
        )

    await session.flush()
    logger.info(
        "notification.dispatched",
        area_id=delivery.area_id,
        delivery_id=delivery.id,
        moment=moment,
        push_ok=push_ok,
        sms_ok=sms_ok,
    )


async def enqueue_notification(*, delivery_id: int, moment: str) -> bool:
    """Put a notify_task on the arq queue. Best-effort (never breaks the request)."""
    from arq import create_pool
    from arq.connections import RedisSettings

    from app.core.config import settings

    try:
        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        try:
            await pool.enqueue_job("notify_task", delivery_id, moment)
        finally:
            await pool.aclose()
        return True
    except Exception:  # noqa: BLE001 — a queue hiccup must not break the trigger
        logger.warning("notification.enqueue_failed", delivery_id=delivery_id, moment=moment)
        return False
