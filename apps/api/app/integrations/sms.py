"""SmsHttpAdapter — Zenvia primary + Twilio fallback (DRV-007).

Production impl. Secrets (tokens) come only from settings/env. Outbound URLs pass
the SSRF guard. A provider failure returns False so the caller can degrade (retry
later / alternate channel) without raising into the request path.
"""

from __future__ import annotations

import structlog

from app.integrations.http import SsrfBlockedError, assert_safe_url, build_client

logger = structlog.get_logger("integrations.sms")


class SmsHttpAdapter:
    """Async OTP delivery with Zenvia→Twilio fallback."""

    def __init__(
        self,
        *,
        zenvia_url: str,
        zenvia_token: str | None,
        twilio_url: str | None,
        twilio_token: str | None,
        allowlist: set[str],
    ) -> None:
        self._zenvia_url = zenvia_url
        self._zenvia_token = zenvia_token
        self._twilio_url = twilio_url
        self._twilio_token = twilio_token
        self._allowlist = allowlist

    async def send_otp(self, phone_e164: str, code: str) -> bool:
        if await self._send(self._zenvia_url, self._zenvia_token, phone_e164, code):
            return True
        if self._twilio_url:
            return await self._send(self._twilio_url, self._twilio_token, phone_e164, code)
        return False

    async def _send(self, url: str | None, token: str | None, phone: str, code: str) -> bool:
        if not url:
            return False
        try:
            assert_safe_url(url, allowlist=self._allowlist)
        except SsrfBlockedError:
            logger.error("sms_ssrf_blocked")
            return False
        try:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            body = {"to": phone, "message": f"Jaxego: seu codigo e {code}"}
            async with build_client() as client:
                # Body intentionally minimal; no PII beyond the destination phone.
                resp = await client.post(url, json=body, headers=headers)
            return resp.status_code in {200, 201, 202}
        except Exception:  # noqa: BLE001 — provider error -> False (degrade)
            logger.warning("sms_provider_error")
            return False
