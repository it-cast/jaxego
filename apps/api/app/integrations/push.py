"""PushVapidAdapter — Web Push via pywebpush (staging/production only).

`pywebpush.webpush()` is synchronous and does the aes128gcm encryption + VAPID
signing; it runs INSIDE the arq worker (never the request — skill push). The
payload carries ZERO PII (LOW-5): only `delivery_id` + deep link + title. The
VAPID private key is a secret read from settings (env only — Gate 8). Any send
error degrades silently (returns False) — a failed push never breaks the dispatch.

pywebpush is imported lazily so dev/test (which use the Stub via the factory) do
not need the runtime dependency installed to import this module.
"""

from __future__ import annotations

import json
from typing import Any, cast

import structlog

from app.integrations.base import PushMessage

logger = structlog.get_logger("integrations.push")


class PushVapidAdapter:
    """Web Push VAPID sender (pywebpush). Degrades silently on failure."""

    def __init__(
        self, *, private_key: str | None, public_key: str | None, claim_sub: str
    ) -> None:
        self._private_key = private_key
        self._public_key = public_key
        self._claim_sub = claim_sub

    async def send(self, message: PushMessage) -> bool:
        """Encrypt + send the push (aes128gcm + VAPID). False on any failure."""
        if not self._private_key:
            # No key configured — degrade silently (polling fallback, skill push).
            logger.warning("push.skipped_no_key", delivery_id=message.delivery_id)
            return False
        try:
            from pywebpush import webpush  # lazy import — runtime-only dep

            # Payload — ZERO PII (LOW-5 / TH-7): delivery_id + deep link + title.
            payload = json.dumps(
                {
                    "delivery_id": message.delivery_id,
                    "deep_link": message.deep_link,
                    "title": message.title,
                }
            )
            webpush(
                subscription_info=cast("dict[str, Any]", message.subscription),
                data=payload,
                vapid_private_key=self._private_key,
                vapid_claims={"sub": self._claim_sub},
                content_encoding="aes128gcm",  # GCM disabled (jun/2024)
            )
            return True
        except Exception as exc:  # noqa: BLE001 — degrade silently (skill push)
            # No PII to log — only the failure shape and the delivery id (A09).
            logger.warning(
                "push.failed", delivery_id=message.delivery_id, error=type(exc).__name__
            )
            return False
