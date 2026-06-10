"""OTP of SMS — server-side generation, aware-UTC expiry, attempt lockout.

TD-010: every datetime is aware UTC (`datetime.now(UTC)` + `ensure_aware_utc` on
DB reads); never `utcnow()`. TH-05/A04/A07: 6-digit code, 10-min TTL, max 5
attempts, constant-time comparison (`secrets.compare_digest`). The state (code
hash, attempts, expiry) is persisted by the service; this module is pure logic.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from app.db.mixins import ensure_aware_utc

OTP_TTL = timedelta(minutes=10)
OTP_MAX_ATTEMPTS = 5
# Resend rate limit (TH-05): 3 sends / 15 min per account+IP (enforced at router).
OTP_RESEND_LIMIT = 3
OTP_RESEND_WINDOW = timedelta(minutes=15)


def new_otp() -> str:
    """A fresh cryptographically-random 6-digit code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def expires_at(now: datetime | None = None) -> datetime:
    """Aware-UTC expiry instant for a code generated `now` (TD-010)."""
    base = now or datetime.now(UTC)
    return base + OTP_TTL


def is_expired(created_at: datetime, now: datetime | None = None) -> bool:
    """True when more than OTP_TTL elapsed since `created_at` (aware UTC).

    `created_at` read from the DB may be naive — coerce it (TD-010 read boundary).
    """
    current = now or datetime.now(UTC)
    return current - ensure_aware_utc(created_at) > OTP_TTL


def verify_code(expected: str, provided: str) -> bool:
    """Constant-time OTP comparison (A07 — never `==`)."""
    return secrets.compare_digest(expected, provided)


def attempts_exhausted(attempts: int) -> bool:
    """True once the attempt counter reaches the lockout threshold."""
    return attempts >= OTP_MAX_ATTEMPTS
