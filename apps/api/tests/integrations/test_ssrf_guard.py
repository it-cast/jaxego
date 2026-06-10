"""SSRF guard for the adapter HTTP client (TH-02/TH-03, owasp A10).

`assert_safe_url` must reject any host outside the allowlist AND any host that
resolves to a private / link-local / loopback IP (cloud metadata 169.254.169.254
is the canonical attack). It must accept an allowlisted public host.
"""

from __future__ import annotations

import pytest
from app.integrations.http import SsrfBlockedError, assert_safe_url


def test_rejects_host_outside_allowlist() -> None:
    with pytest.raises(SsrfBlockedError):
        assert_safe_url("https://evil.example.com/x", allowlist={"minhareceita.org"})


def test_rejects_link_local_metadata_ip() -> None:
    # 169.254.169.254 is the cloud metadata endpoint — even if allowlisted by
    # name, the resolved IP is link-local and must be refused.
    with pytest.raises(SsrfBlockedError):
        assert_safe_url(
            "http://169.254.169.254/latest/meta-data/",
            allowlist={"169.254.169.254"},
        )


def test_rejects_loopback() -> None:
    with pytest.raises(SsrfBlockedError):
        assert_safe_url("http://127.0.0.1:8080/", allowlist={"127.0.0.1"})


def test_rejects_private_range() -> None:
    with pytest.raises(SsrfBlockedError):
        assert_safe_url("http://10.0.0.5/internal", allowlist={"10.0.0.5"})


def test_accepts_allowlisted_public_host() -> None:
    # A public, allowlisted host must pass (uses a stable well-known public IP).
    assert_safe_url("https://brasilapi.com.br/api/cnpj/v1/x", allowlist={"brasilapi.com.br"})
