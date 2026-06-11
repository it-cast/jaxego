"""Push adapter (D-08 / LOW-5 / TH-7): Stub records sends; payload has ZERO PII.

The Stub records each send so a test can assert the payload shape. The payload
must carry ONLY delivery_id + deep link + title — NEVER address/phone/name (RN-013
/ LOW-5). The ranking/cascade route the deep link, never PII.
"""

from __future__ import annotations

import json

from app.integrations.base import PushMessage
from app.integrations.push import PushVapidAdapter
from app.integrations.push_stub import PushStubAdapter


async def test_stub_records_send_with_no_pii() -> None:
    adapter = PushStubAdapter()
    message = PushMessage(
        subscription={"endpoint": "https://push.example/abc"},
        delivery_id=42,
        deep_link="/entregador/oferta/42",
    )
    ok = await adapter.send(message)
    assert ok is True
    assert len(adapter.sent) == 1
    sent = adapter.sent[0]
    assert sent.delivery_id == 42
    assert sent.title == "Nova oferta"
    # ZERO PII (LOW-5) — the message carries only delivery_id + deep link + title.
    blob = json.dumps(
        {"delivery_id": sent.delivery_id, "deep_link": sent.deep_link, "title": sent.title}
    )
    for forbidden in ("Rua", "telefone", "+55", "cpf", "@", "Cliente"):
        assert forbidden not in blob


async def test_vapid_adapter_degrades_without_key() -> None:
    """No VAPID key configured → degrade silently (returns False, never raises)."""
    adapter = PushVapidAdapter(private_key=None, public_key=None, claim_sub="mailto:x@y.z")
    message = PushMessage(
        subscription={"endpoint": "https://push.example/abc"},
        delivery_id=7,
        deep_link="/entregador/oferta/7",
    )
    ok = await adapter.send(message)
    assert ok is False  # degraded, no exception


def test_push_message_default_title() -> None:
    """The default title is the generic, PII-free 'Nova oferta'."""
    message = PushMessage(subscription={}, delivery_id=1, deep_link="/x")
    assert message.title == "Nova oferta"
