"""Anti-SSRF validation of the webhook URL (T-08 / TH-05).

Blocks: non-https schemes, missing host, literal private/loopback/link-local IPs,
and the cloud-metadata address 169.254.169.254. Allows a normal public https URL.
DNS-resolving hosts that map to public IPs are not exercised here (no network in
the unit test) — the literal-IP and scheme checks are the deterministic guard.
"""

from __future__ import annotations

import pytest
from app.webhooks.ssrf import WebhookUrlInvalidError, assert_safe_webhook_url


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/webhook",  # not https
        "ftp://example.com/webhook",  # not https
        "https://",  # no host
        "https://127.0.0.1/webhook",  # loopback
        "https://10.0.0.5/webhook",  # private
        "https://192.168.1.10/webhook",  # private
        "https://169.254.169.254/latest/meta-data",  # cloud metadata
        "https://[::1]/webhook",  # ipv6 loopback
        "https://0.0.0.0/webhook",  # unspecified
    ],
)
def test_blocked_urls_raise(url: str) -> None:
    with pytest.raises(WebhookUrlInvalidError):
        assert_safe_webhook_url(url)


def test_public_https_url_passes() -> None:
    # A literal public IP passes (1.1.1.1 is public); a hostname would resolve via DNS.
    assert_safe_webhook_url("https://1.1.1.1/webhook")
