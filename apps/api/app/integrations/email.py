"""EmailSesAdapter — AWS SES confirmation link (D-08).

Production impl. The confirmation endpoint base + SES region come from settings;
credentials only from env. Outbound URL passes the SSRF guard.
"""

from __future__ import annotations

import structlog

from app.integrations.http import SsrfBlockedError, assert_safe_url, build_client

logger = structlog.get_logger("integrations.email")


class EmailSesAdapter:
    """Async confirmation-link sender via an SES-backed HTTP endpoint."""

    def __init__(self, *, send_url: str, api_token: str | None, allowlist: set[str]) -> None:
        self._send_url = send_url
        self._api_token = api_token
        self._allowlist = allowlist

    async def send_confirm_link(self, email: str, token: str) -> bool:
        try:
            assert_safe_url(self._send_url, allowlist=self._allowlist)
        except SsrfBlockedError:
            logger.error("email_ssrf_blocked")
            return False
        try:
            headers = {"Authorization": f"Bearer {self._api_token}"} if self._api_token else {}
            async with build_client() as client:
                resp = await client.post(
                    self._send_url, json={"to": email, "token": token}, headers=headers
                )
            return resp.status_code in {200, 201, 202}
        except Exception:  # noqa: BLE001 — provider error -> False (degrade)
            logger.warning("email_provider_error")
            return False
