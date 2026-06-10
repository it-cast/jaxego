"""Core security primitives: password hashing (argon2id), JWT (HS256), opaque
refresh tokens and TOTP helpers.

Everything here is library-backed and structural — never hand-rolled crypto
(RESEARCH "Don't Hand-Roll"). All datetimes are aware UTC (TD-010).

Sources:
- argon2-cffi PasswordHasher (Pattern 2) — explicit OWASP params (LOW-1).
- PyJWT HS256 with pinned algorithm + required claims (Pattern 3, anti alg:none).
- opaque refresh via secrets.token_urlsafe + sha256 in DB (Pattern 4).
- pyotp TOTP RFC 6238 (valid_window=1).
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing — argon2id with EXPLICIT, pinned parameters (LOW-1 resolved).
#
# specs/stack.yaml says "custo 12" — that is BCRYPT terminology and must NOT be
# applied literally to argon2. We pin the OWASP-recommended argon2id baseline
# (time_cost=2, memory_cost=19456 KiB ~= 19 MiB, parallelism=1), which targets
# ~50-100ms verify on commodity hardware. check_needs_rehash enables a
# transparent parameter upgrade later without forcing password resets.
# ---------------------------------------------------------------------------
ARGON2_TIME_COST = 2
ARGON2_MEMORY_COST = 19_456  # KiB (~19 MiB)
ARGON2_PARALLELISM = 1

_password_hasher = PasswordHasher(
    time_cost=ARGON2_TIME_COST,
    memory_cost=ARGON2_MEMORY_COST,
    parallelism=ARGON2_PARALLELISM,
)

# A fixed dummy hash used to spend ~constant time when the user does not exist,
# defeating account enumeration by timing (RN-011 / A05/A07). Computed once at
# import with the pinned parameters so verify cost matches a real account.
_DUMMY_HASH = _password_hasher.hash("dummy-password-for-constant-time-verify")


def hash_password(raw: str) -> str:
    """Hash a plaintext password with argon2id (pinned params)."""
    return _password_hasher.hash(raw)


def verify_password(stored_hash: str, raw: str) -> tuple[bool, str | None]:
    """Verify a password against a stored hash.

    Returns (ok, new_hash). `new_hash` is non-None only when the stored hash
    used weaker parameters and should be transparently upgraded by the caller.
    """
    try:
        _password_hasher.verify(stored_hash, raw)
    except (VerifyMismatchError, InvalidHashError):
        return False, None
    new_hash = None
    if _password_hasher.check_needs_rehash(stored_hash):
        new_hash = _password_hasher.hash(raw)
    return True, new_hash


def verify_dummy(raw: str) -> None:
    """Run a verify against the dummy hash to spend ~constant time.

    Called on the login path when the user does not exist so that the response
    time does not reveal account existence (anti-enumeration, RN-011).
    """
    try:
        _password_hasher.verify(_DUMMY_HASH, raw)
    except (VerifyMismatchError, InvalidHashError):
        pass


# ---------------------------------------------------------------------------
# TOTP (RFC 6238) — pyotp. Secret generated and validated server-side; the
# client only ever types the 6-digit code. valid_window=1 (~+/-30s skew).
# Replay defence (persisting the last accepted code/window) lives in the auth
# service, since it needs the user row.
# ---------------------------------------------------------------------------
TOTP_VALID_WINDOW = 1


def generate_totp_secret() -> str:
    """Generate a fresh base32 TOTP secret."""
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, account_name: str, issuer: str | None = None) -> str:
    """Build an otpauth:// URI for QR enrolment (shown once, never re-exposed)."""
    return pyotp.TOTP(secret).provisioning_uri(
        name=account_name,
        issuer_name=issuer or settings.jwt_issuer,
    )


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code with skew tolerance (valid_window=1)."""
    return pyotp.TOTP(secret).verify(code, valid_window=TOTP_VALID_WINDOW)


def current_totp_window(secret: str) -> int:
    """Return the current TOTP counter (timecode) for replay tracking."""
    totp = pyotp.TOTP(secret)
    return totp.timecode(datetime.now(UTC))


# ---------------------------------------------------------------------------
# JWT access token — HS256, claims pinned, algorithm pinned on decode (Pattern 3).
#
# HS256 is locked by ADR-005 and correct here: a single FastAPI process both
# issues AND validates the token, so a symmetric secret is appropriate (OWASP
# A02 decision table). NOTE: if validation ever moves to a second process
# (gateway/worker), migrating to RS256/ES256 (asymmetric, multi-validator —
# e.g. Menu Certo) should be a FUTURE ADR, not a blocker now (LOW-2 resolved:
# PyJWT pinned).
#
# decode pins algorithms=["HS256"] (defeats alg:none) AND requires the critical
# claims, so a stripped token is rejected.
# ---------------------------------------------------------------------------
_REQUIRED_CLAIMS = ["exp", "iat", "iss", "aud", "sub", "jti"]


def encode_access(user_id: int, area_scope: int | None, role: str) -> str:
    """Issue a 15-minute HS256 access token with pinned claims (aware UTC)."""
    now = datetime.now(UTC)  # AWARE — TD-010
    payload: dict[str, object] = {
        "sub": str(user_id),
        "area_scope": area_scope,  # None for platform admin (audited bypass)
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access(token: str) -> dict[str, object]:
    """Decode + validate an access token. Raises jwt.PyJWTError on any failure."""
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],  # PINNED — mitigates alg:none
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
        options={"require": _REQUIRED_CLAIMS},
    )


# ---------------------------------------------------------------------------
# Opaque refresh token (Pattern 4). The client holds a 256-bit opaque value;
# only its SHA-256 is stored in DB. Rotation + reuse-detection live in the auth
# service (they need the DB row + token family).
# ---------------------------------------------------------------------------
def new_refresh_token() -> tuple[str, str]:
    """Return (raw_value_for_client, sha256_hex_for_db)."""
    raw = secrets.token_urlsafe(32)  # 256 bits
    return raw, hash_refresh_token(raw)


def hash_refresh_token(raw: str) -> str:
    """SHA-256 hex of a refresh token (deterministic; for DB lookup)."""
    return hashlib.sha256(raw.encode()).hexdigest()


def compare_secret(a: str, b: str) -> bool:
    """Timing-safe comparison of two secrets (A02/A08)."""
    return secrets.compare_digest(a, b)
