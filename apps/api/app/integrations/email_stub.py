"""EmailStubAdapter — dev/test only; captures the confirmation link."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CapturedEmail:
    email: str
    token: str


class EmailStubAdapter:
    """Captures confirmation e-mails in memory (no network)."""

    def __init__(self) -> None:
        self.sent: list[CapturedEmail] = []

    async def send_confirm_link(self, email: str, token: str) -> bool:
        self.sent.append(CapturedEmail(email=email, token=token))
        return True
