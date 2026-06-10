"""SmsStubAdapter — dev/test only; captures the OTP instead of sending it."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CapturedSms:
    phone_e164: str
    code: str


class SmsStubAdapter:
    """Captures sent OTPs in memory (no network); tests can inspect `sent`."""

    def __init__(self) -> None:
        self.sent: list[CapturedSms] = []

    async def send_otp(self, phone_e164: str, code: str) -> bool:
        self.sent.append(CapturedSms(phone_e164=phone_e164, code=code))
        return True
