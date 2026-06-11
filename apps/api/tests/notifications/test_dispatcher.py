"""Multichannel dispatcher (RN-018 / REQ-049): fallback push→email; SMS só "a caminho".

Stubs let us force push success/failure and inspect channel attempts. The invariants:
- accepted/delivered: push only; on failure → email fallback (push→email).
- on_the_way: push + SMS (the ONLY moment SMS fires) + email fallback.
- every attempt is recorded in `notifications` (channel + status, no PII).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.deliveries.models import Delivery, Recipient
from app.integrations.base import PushMessage
from app.notifications.dispatcher import notify
from app.notifications.models import Notification, PushSubscription
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass
class FailingPush:
    sent: list[PushMessage] = field(default_factory=list)

    async def send(self, message: PushMessage) -> bool:
        self.sent.append(message)
        return False  # always fails → triggers email fallback


@dataclass
class OkPush:
    sent: list[PushMessage] = field(default_factory=list)

    async def send(self, message: PushMessage) -> bool:
        self.sent.append(message)
        return True


@dataclass
class CaptureSms:
    sent: list[tuple[str, str]] = field(default_factory=list)

    async def send_otp(self, phone_e164: str, code: str) -> bool:
        self.sent.append((phone_e164, code))
        return True


@dataclass
class CaptureEmail:
    sent: list[tuple[str, str]] = field(default_factory=list)

    async def send_confirm_link(self, email: str, token: str) -> bool:
        self.sent.append((email, token))
        return True


@dataclass
class NotifySeed:
    area_id: int
    delivery_id: int


@pytest_asyncio.fixture
async def notify_seed(session_factory: async_sessionmaker[AsyncSession]) -> NotifySeed:
    async with session_factory() as s:
        area = Area(codename="padua", name="Pádua", config={})
        s.add(area)
        await s.flush()
        recipient = Recipient(
            area_id=area.id,
            name="Cliente",
            phone_e164="+5522988887777",
            email="cliente@example.com",
            deliveries_count=0,
            refusals_count=0,
        )
        s.add(recipient)
        await s.flush()
        # A neighborhood-free delivery (dropoff_neighborhood_id can reference nothing
        # for the notification test since we never join it). Use a real one to be safe.
        from app.neighborhoods.models import Neighborhood

        nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
        s.add(nbhd)
        await s.flush()
        from app.merchants.models import Merchant

        merchant = Merchant(
            area_id=area.id,
            account_type="cnpj",
            document="11222333000181",
            trade_name="Loja",
            category="restaurante",
            phone_e164="+5522999991111",
            email="loja@example.com",
            status="active",
        )
        s.add(merchant)
        await s.flush()
        delivery = Delivery(
            area_id=area.id,
            merchant_id=merchant.id,
            recipient_id=recipient.id,
            state="COLETADA",
            dispatch_mode="direct",
            payment_method="direct",
            proof_method="photo",
            pickup_address="a",
            dropoff_address="b",
            dropoff_neighborhood_id=nbhd.id,
            fee_cents=0,
            items_quantity=1,
            public_token="NOTIFTOKEN0000000000000001",
            origin="manual",
        )
        s.add(delivery)
        await s.flush()
        await s.commit()
        return NotifySeed(area_id=area.id, delivery_id=delivery.id)


async def _recipient(s: AsyncSession, delivery: Delivery) -> Recipient | None:
    return await s.get(Recipient, delivery.recipient_id) if delivery.recipient_id else None


async def _channels(s: AsyncSession, delivery_id: int) -> list[tuple[str, str, str]]:
    rows = (
        await s.execute(
            select(Notification.moment, Notification.channel, Notification.status).where(
                Notification.delivery_id == delivery_id
            )
        )
    ).all()
    return [(m, c, st) for m, c, st in rows]


@pytest.mark.asyncio
async def test_push_failure_falls_back_to_email(
    session_factory: async_sessionmaker[AsyncSession], notify_seed: NotifySeed
) -> None:
    """accepted: push fails (no subscription) → email fallback recorded."""
    push, sms, email = FailingPush(), CaptureSms(), CaptureEmail()
    async with session_factory() as s:
        delivery = await s.get(Delivery, notify_seed.delivery_id)
        await notify(
            s,
            delivery=delivery,
            recipient=await _recipient(s, delivery),
            moment="accepted",
            push=push,
            sms=sms,
            email=email,
        )
        await s.commit()
        chans = await _channels(s, notify_seed.delivery_id)
    # No subscription → push skipped; email fallback sent. SMS NOT fired (accepted).
    channels = {c for _, c, _ in chans}
    assert "email" in channels
    assert "sms" not in channels
    assert len(email.sent) == 1
    assert len(sms.sent) == 0


@pytest.mark.asyncio
async def test_on_the_way_sends_sms(
    session_factory: async_sessionmaker[AsyncSession], notify_seed: NotifySeed
) -> None:
    """on_the_way is the ONLY moment SMS fires (RN-018)."""
    push, sms, email = OkPush(), CaptureSms(), CaptureEmail()
    # Register a push subscription so push actually sends.
    async with session_factory() as s:
        s.add(
            PushSubscription(
                area_id=notify_seed.area_id,
                delivery_id=notify_seed.delivery_id,
                endpoint="https://push.example/abc",
                keys_json=json.dumps({"p256dh": "x", "auth": "y"}),
            )
        )
        await s.commit()
    async with session_factory() as s:
        delivery = await s.get(Delivery, notify_seed.delivery_id)
        await notify(
            s,
            delivery=delivery,
            recipient=await _recipient(s, delivery),
            moment="on_the_way",
            push=push,
            sms=sms,
            email=email,
        )
        await s.commit()
        chans = await _channels(s, notify_seed.delivery_id)
    assert len(sms.sent) == 1
    assert sms.sent[0][0] == "+5522988887777"
    # The SMS carries the tracking link (token only — no PII).
    assert sms.sent[0][1] == "/r/NOTIFTOKEN0000000000000001"
    channels = {c for _, c, _ in chans}
    assert "sms" in channels and "push" in channels
    # push succeeded → no email fallback.
    assert len(email.sent) == 0


@pytest.mark.asyncio
async def test_delivered_no_sms(
    session_factory: async_sessionmaker[AsyncSession], notify_seed: NotifySeed
) -> None:
    push, sms, email = FailingPush(), CaptureSms(), CaptureEmail()
    async with session_factory() as s:
        delivery = await s.get(Delivery, notify_seed.delivery_id)
        await notify(
            s,
            delivery=delivery,
            recipient=await _recipient(s, delivery),
            moment="delivered",
            push=push,
            sms=sms,
            email=email,
        )
        await s.commit()
    # SMS never fires outside on_the_way.
    assert len(sms.sent) == 0
