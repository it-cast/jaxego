"""Outbound webhook signing (Stripe scheme) + a ULID-like event id (D-06).

The signature header is `X-Jaxego-Signature: t=<unix_ts>,v1=<hex>` where
`hex = HMAC-SHA256(secret, f"{t}.{raw_body}")` — the timestamp is part of the
signed material so a receiver can enforce a 5-min anti-replay window. The
`X-Jaxego-Event-Id` is a 26-char ULID (Crockford base32, time-ordered) the
receiver dedups on. No new dependency — the ULID is built from the millisecond
timestamp + entropy, like `deliveries._new_public_token`.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

# Crockford base32 (no I/L/O/U) — ULID alphabet.
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def new_event_id(*, now_ms: int | None = None) -> str:
    """A 26-char ULID: 48-bit millisecond timestamp + 80 bits of entropy.

    Time-ordered (the first 10 chars encode the ms timestamp) so event ids sort
    chronologically; the trailing 16 chars are random (anti-collision / anti-guess).
    """
    import time

    ts = now_ms if now_ms is not None else int(time.time() * 1000)
    # 48-bit timestamp → 10 Crockford chars.
    time_part = ""
    for _ in range(10):
        time_part = _CROCKFORD[ts & 0x1F] + time_part
        ts >>= 5
    rand_part = "".join(secrets.choice(_CROCKFORD) for _ in range(16))
    return time_part + rand_part


def sign_payload(secret: str, *, timestamp: int, raw_body: bytes) -> str:
    """Build the `t=...,v1=...` signature header value (Stripe scheme — D-06).

    The signed material is `f"{timestamp}.{raw_body}"` so the timestamp is bound
    into the MAC (the receiver re-derives it and rejects an old `t`).
    """
    signed = f"{timestamp}.".encode() + raw_body
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def verify_signature(
    secret: str, *, header: str, raw_body: bytes, tolerance_seconds: int = 300
) -> bool:
    """Verify a `t=...,v1=...` header (used by tests + a reference receiver).

    Recomputes the MAC over `f"{t}.{raw_body}"` and compares with
    `hmac.compare_digest` (NEVER ==, anti-timing — TH-07). Rejects a timestamp
    outside ±`tolerance_seconds` (5-min anti-replay window — D-06).
    """
    import time

    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    t_raw = parts.get("t")
    v1 = parts.get("v1")
    if not t_raw or not v1:
        return False
    try:
        timestamp = int(t_raw)
    except ValueError:
        return False
    if abs(int(time.time()) - timestamp) > tolerance_seconds:
        return False
    expected = sign_payload(secret, timestamp=timestamp, raw_body=raw_body)
    expected_v1 = expected.split("v1=", 1)[1]
    return hmac.compare_digest(expected_v1, v1)
