"""Shared httpx client + SSRF guard for the external adapters (owasp A10).

`assert_safe_url` is the single chokepoint every outbound URL passes through. It
(1) requires the host to be in the caller's allowlist, and (2) resolves every IP
the host maps to and refuses private / link-local / loopback / reserved ranges
(cloud metadata 169.254.169.254 is the canonical SSRF target). Adapters call it
BEFORE connecting and AFTER any redirect (clients run with
`follow_redirects=False`).
"""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Iterable
from urllib.parse import urlparse

import httpx

from app.core.exceptions import AppError

# Short timeout for every external call (A10 / resilience — never hang a request).
DEFAULT_TIMEOUT = httpx.Timeout(5.0, connect=3.0)


class SsrfBlockedError(AppError):
    """An outbound URL failed the SSRF guard (host not allowed / private IP)."""

    status_code = 502
    code = "ssrf_blocked"

    def __init__(self, host: str) -> None:
        # The host is operator-facing context, not user PII.
        super().__init__(f"Destino externo bloqueado por segurança: {host}")


def _is_forbidden_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """True for any non-routable / internal address (defence in depth)."""
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def assert_safe_url(url: str, *, allowlist: Iterable[str]) -> None:
    """Raise SsrfBlockedError unless `url`'s host is allowlisted AND public.

    Validates host membership first (cheap), then resolves the host and rejects
    if ANY resolved address is internal. Must be called before connecting and
    re-called after a redirect with the new Location.
    """
    allowed = {h.lower() for h in allowlist}
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()

    if not host or host not in allowed:
        raise SsrfBlockedError(host or "<empty>")

    # A literal IP host: validate it directly.
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if _is_forbidden_ip(literal):
            raise SsrfBlockedError(host)
        return

    # Resolve the hostname; reject if any address is internal.
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise SsrfBlockedError(host) from exc

    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if _is_forbidden_ip(ip):
            raise SsrfBlockedError(host)


def build_client(timeout: httpx.Timeout | None = None) -> httpx.AsyncClient:
    """Create an httpx async client with redirects DISABLED (revalidate manually)."""
    return httpx.AsyncClient(timeout=timeout or DEFAULT_TIMEOUT, follow_redirects=False)
