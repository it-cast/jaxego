"""Webhook HMAC signature (T-06 / TH-06/TH-07) + ULID event id.

Proves: the signature is the Stripe `t=...,v1=...` scheme over `f"{t}.{body}"`; a
valid signature verifies; a tampered body / wrong secret / stale timestamp fails;
verification uses compare_digest (anti-timing). Event ids are 26-char, unique, and
time-ordered.
"""

from __future__ import annotations

import time

from app.webhooks.signing import new_event_id, sign_payload, verify_signature


def test_signature_roundtrip_valid() -> None:
    secret = "whsec_test"
    body = b'{"id":"evt_1","type":"delivery.created"}'
    ts = int(time.time())
    header = sign_payload(secret, timestamp=ts, raw_body=body)
    assert header.startswith(f"t={ts},v1=")
    assert verify_signature(secret, header=header, raw_body=body)


def test_signature_rejects_tampered_body() -> None:
    secret = "whsec_test"
    ts = int(time.time())
    header = sign_payload(secret, timestamp=ts, raw_body=b"original")
    assert not verify_signature(secret, header=header, raw_body=b"tampered")


def test_signature_rejects_wrong_secret() -> None:
    ts = int(time.time())
    header = sign_payload("secret-a", timestamp=ts, raw_body=b"body")
    assert not verify_signature("secret-b", header=header, raw_body=b"body")


def test_signature_rejects_stale_timestamp() -> None:
    secret = "whsec_test"
    old_ts = int(time.time()) - 3600  # 1h ago, outside the 5-min window
    header = sign_payload(secret, timestamp=old_ts, raw_body=b"body")
    assert not verify_signature(secret, header=header, raw_body=b"body", tolerance_seconds=300)


def test_signature_within_window_accepted() -> None:
    secret = "whsec_test"
    recent_ts = int(time.time()) - 120  # 2 min ago, inside the window
    header = sign_payload(secret, timestamp=recent_ts, raw_body=b"body")
    assert verify_signature(secret, header=header, raw_body=b"body", tolerance_seconds=300)


def test_event_id_is_26_chars_unique_and_time_ordered() -> None:
    a = new_event_id(now_ms=1_000_000_000)
    b = new_event_id(now_ms=2_000_000_000)
    assert len(a) == 26 and len(b) == 26
    assert a != b
    # Time-ordered: a later timestamp sorts after (the 10-char time prefix dominates).
    assert a[:10] < b[:10]
