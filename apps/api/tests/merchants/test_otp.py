"""OTP of SMS — aware UTC expiry + attempt lockout (TD-010, TH-05, A04/A07)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.merchants import otp


def test_new_otp_is_six_digits() -> None:
    code = otp.new_otp()
    assert len(code) == 6
    assert code.isdigit()


def test_is_expired_uses_aware_utc() -> None:
    fresh = datetime.now(UTC)
    assert otp.is_expired(fresh) is False
    old = datetime.now(UTC) - otp.OTP_TTL - timedelta(seconds=1)
    assert otp.is_expired(old) is True


def test_is_expired_coerces_naive_db_value() -> None:
    # Some drivers return naive datetimes; the helper must coerce to aware UTC
    # and NOT raise "can't compare offset-naive and offset-aware".
    naive_fresh = datetime.now(UTC).replace(tzinfo=None)
    assert otp.is_expired(naive_fresh) is False


def test_verify_constant_time_and_match() -> None:
    code = otp.new_otp()
    assert otp.verify_code(code, code) is True
    assert otp.verify_code(code, "000000" if code != "000000" else "111111") is False


def test_attempts_exhausted_locks() -> None:
    assert otp.attempts_exhausted(otp.OTP_MAX_ATTEMPTS) is True
    assert otp.attempts_exhausted(otp.OTP_MAX_ATTEMPTS - 1) is False


@pytest.mark.parametrize("attempts", [0, 1, 4])
def test_attempts_not_exhausted_below_threshold(attempts: int) -> None:
    assert otp.attempts_exhausted(attempts) is False
