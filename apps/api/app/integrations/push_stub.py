"""PushStubAdapter — records sends in-memory, no network (dev/test).

The Stub lets the dispatch tests assert that a push WAS enqueued and that its
payload carries ZERO PII (LOW-5 — only delivery_id + deep link + title). Each
adapter instance keeps its own `sent` list so a test can inspect it.
"""

from __future__ import annotations

from app.integrations.base import PushMessage


class PushStubAdapter:
    """In-memory push recorder (no network). Inspect `.sent` in tests."""

    def __init__(self) -> None:
        self.sent: list[PushMessage] = []

    async def send(self, message: PushMessage) -> bool:
        """Record the send and report success (degrade-safe contract)."""
        self.sent.append(message)
        return True
