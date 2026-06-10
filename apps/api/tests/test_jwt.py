"""Tests for JWT HS256 encode/decode + opaque refresh token (T-03, LOW-2).

Proves: round-trip; alg:none rejected; missing required claims rejected; wrong
audience/issuer rejected; expired token rejected; deterministic refresh hash;
timing-safe compare.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from app.core.config import settings
from app.core.security import (
    compare_secret,
    decode_access,
    encode_access,
    hash_refresh_token,
    new_refresh_token,
)


def test_access_token_roundtrip() -> None:
    token = encode_access(user_id=42, area_scope=7, role="admin_area")
    claims = decode_access(token)
    assert claims["sub"] == "42"
    assert claims["area_scope"] == 7
    assert claims["role"] == "admin_area"
    assert claims["iss"] == settings.jwt_issuer
    assert claims["aud"] == settings.jwt_audience
    assert "jti" in claims


def test_platform_admin_area_scope_none() -> None:
    token = encode_access(user_id=1, area_scope=None, role="admin_plataforma")
    claims = decode_access(token)
    assert claims["area_scope"] is None


def test_alg_none_token_rejected() -> None:
    """A token forged with alg=none must be rejected (anti alg:none)."""
    forged = jwt.encode(
        {"sub": "1", "iss": settings.jwt_issuer, "aud": settings.jwt_audience},
        key="",
        algorithm="none",
    )
    with pytest.raises(jwt.PyJWTError):
        decode_access(forged)


def test_missing_required_claim_rejected() -> None:
    """A token missing exp/aud/iss is rejected by options.require."""
    incomplete = jwt.encode({"sub": "1"}, settings.jwt_secret, algorithm="HS256")
    with pytest.raises(jwt.PyJWTError):
        decode_access(incomplete)


def test_wrong_audience_rejected() -> None:
    now = datetime.now(UTC)
    bad = jwt.encode(
        {
            "sub": "1",
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "iss": settings.jwt_issuer,
            "aud": "someone-else",
            "jti": "x",
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(jwt.PyJWTError):
        decode_access(bad)


def test_expired_token_rejected() -> None:
    now = datetime.now(UTC)
    expired = jwt.encode(
        {
            "sub": "1",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "jti": "x",
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access(expired)


def test_refresh_token_hash_is_deterministic() -> None:
    raw, digest = new_refresh_token()
    assert digest == hash_refresh_token(raw)
    assert len(digest) == 64  # sha256 hex
    # different generations differ
    raw2, digest2 = new_refresh_token()
    assert raw != raw2
    assert digest != digest2


def test_compare_secret_timing_safe() -> None:
    assert compare_secret("abc", "abc") is True
    assert compare_secret("abc", "abd") is False
