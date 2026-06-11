"""Anti-SSRF validation for the area-configured webhook URL (TH-05 / A10).

Unlike the external adapters (which call a FIXED allowlist of hosts), a webhook
URL is chosen by the area admin — there is no allowlist. So the guard is:
  1. scheme MUST be https (no http, no file://, no gopher://, …)
  2. a host MUST be present
  3. EVERY IP the host resolves to MUST be public — reject loopback / private /
     link-local / reserved / multicast / unspecified, and explicitly the cloud
     metadata address 169.254.169.254 (the canonical SSRF target).

It reuses `_is_forbidden_ip` from the adapters' SSRF guard (single source of truth
for "non-routable") so the two stay consistent. Validated at REGISTRATION (T-08)
and re-checked by the delivery job before each POST (defence in depth).
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.core.exceptions import AppError
from app.integrations.http import _is_forbidden_ip


class WebhookUrlInvalidError(AppError):
    """The configured webhook URL is not https or resolves to a private host (TH-05)."""

    status_code = 422
    code = "webhook_url_invalid"

    def __init__(self, detail: str) -> None:
        super().__init__(f"URL de webhook inválida: {detail}")


def assert_safe_webhook_url(url: str) -> None:
    """Raise WebhookUrlInvalidError unless `url` is https AND resolves only to public IPs."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise WebhookUrlInvalidError("use https")
    host = (parsed.hostname or "").lower()
    if not host:
        raise WebhookUrlInvalidError("host ausente")

    # A literal IP host: validate directly (also catches 169.254.169.254 typed raw).
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if _is_forbidden_ip(literal):
            raise WebhookUrlInvalidError("endereço de host privado/interno bloqueado")
        return

    # Resolve and reject if ANY address is internal (DNS-rebinding defence).
    try:
        infos = socket.getaddrinfo(host, parsed.port or 443)
    except socket.gaierror as exc:
        raise WebhookUrlInvalidError("host não resolvível") from exc

    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if _is_forbidden_ip(ip):
            raise WebhookUrlInvalidError("host resolve para endereço interno bloqueado")
