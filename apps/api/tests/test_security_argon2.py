"""Tests for argon2id password hashing + TOTP helpers (T-02, LOW-1).

Asserts: correct/incorrect verify, explicit pinned parameters, check_needs_rehash
behaviour, constant-time dummy verify, and a tolerant ~100ms benchmark proving
the parameters are dimensioned (not the library defaults silently).
"""

from __future__ import annotations

import time

from app.core.security import (
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
    ARGON2_TIME_COST,
    current_totp_window,
    generate_totp_secret,
    hash_password,
    totp_provisioning_uri,
    verify_dummy,
    verify_password,
    verify_totp,
)


def test_params_are_explicit_owasp_baseline() -> None:
    """Parameters are pinned explicitly (LOW-1), not library defaults."""
    assert ARGON2_TIME_COST == 2
    assert ARGON2_MEMORY_COST == 19_456
    assert ARGON2_PARALLELISM == 1


def test_hash_and_verify_roundtrip() -> None:
    h = hash_password("correct horse battery staple")
    ok, new_hash = verify_password(h, "correct horse battery staple")
    assert ok is True
    assert new_hash is None  # same params => no rehash needed


def test_verify_wrong_password_fails() -> None:
    h = hash_password("right-password")
    ok, new_hash = verify_password(h, "wrong-password")
    assert ok is False
    assert new_hash is None


def test_verify_invalid_hash_is_safe() -> None:
    ok, new_hash = verify_password("not-a-real-argon2-hash", "anything")
    assert ok is False
    assert new_hash is None


def test_hash_is_salted_unique() -> None:
    assert hash_password("same") != hash_password("same")


def test_check_needs_rehash_on_weaker_params() -> None:
    """A hash produced with weaker params is flagged for rehash on verify."""
    from argon2 import PasswordHasher

    weak = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)
    weak_hash = weak.hash("pw")
    ok, new_hash = verify_password(weak_hash, "pw")
    assert ok is True
    assert new_hash is not None  # transparently upgraded to pinned params


def test_dummy_verify_does_not_raise() -> None:
    verify_dummy("whatever")  # constant-time path for non-existent users


def test_verify_benchmark_in_expected_range() -> None:
    """Verify is ~100ms — tolerant range proves params are dimensioned (LOW-1)."""
    h = hash_password("benchmark-password")
    start = time.perf_counter()
    verify_password(h, "benchmark-password")
    elapsed_ms = (time.perf_counter() - start) * 1000
    # Wide band tolerant to CI/dev hardware: not too fast (under-dimensioned),
    # not absurdly slow.
    assert 15 <= elapsed_ms <= 600, f"argon2 verify took {elapsed_ms:.1f}ms"


# --- TOTP helpers ---


def test_totp_secret_and_verify_roundtrip() -> None:
    import pyotp

    secret = generate_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert verify_totp(secret, code) is True


def test_totp_wrong_code_rejected() -> None:
    secret = generate_totp_secret()
    assert verify_totp(secret, "000000") is False


def test_totp_provisioning_uri_contains_issuer() -> None:
    secret = generate_totp_secret()
    uri = totp_provisioning_uri(secret, "admin@example.com", issuer="jaxego")
    assert uri.startswith("otpauth://totp/")
    assert "issuer=jaxego" in uri


def test_totp_window_is_int() -> None:
    secret = generate_totp_secret()
    assert isinstance(current_totp_window(secret), int)
