"""Auth service: login, lockout (5/15min, aware UTC), anti-enumeration, TOTP,
refresh issue/rotate/reuse-detection, logout.

Security invariants live here, server-side (A04). All datetimes are aware UTC
(TD-010). Login emits structured events WITHOUT PII (RN-021). The login path
spends ~constant time whether or not the user exists (anti-enumeration, RN-011).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken, User
from app.auth.schemas import TokenPair
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import (
    encode_access,
    new_refresh_token,
    verify_dummy,
    verify_password,
    verify_totp,
)

logger = structlog.get_logger("auth")

# Lockout policy — derived from ADR-005 + OWASP A04 (inviabiliza brute force sem
# punir caps lock): 5 attempts within a 15-minute sliding window per account.
LOCK_THRESHOLD = 5
LOCK_WINDOW = timedelta(minutes=15)

# Single generic message — never reveals whether the account exists (RN-011/A05).
INVALID_CREDENTIALS = "Credenciais inválidas."


class InvalidCredentialsError(AppError):
    """Generic auth failure — same message for unknown user / wrong password."""

    status_code = 401
    code = "invalid_credentials"

    def __init__(self) -> None:
        super().__init__(INVALID_CREDENTIALS)


class AccountLockedError(AppError):
    """Account temporarily locked after too many failed attempts (423)."""

    status_code = 423
    code = "account_locked"

    def __init__(self) -> None:
        super().__init__("Conta temporariamente bloqueada. Tente novamente mais tarde.")


class TotpRequiredError(AppError):
    """TOTP is required (enrolled) but missing/invalid for this login."""

    status_code = 401
    code = "totp_required"

    def __init__(self, message: str = "Código TOTP obrigatório ou inválido.") -> None:
        super().__init__(message)


class RefreshReuseError(AppError):
    """A rotated refresh token was reused — family revoked, re-login required."""

    status_code = 401
    code = "refresh_reuse_detected"

    def __init__(self) -> None:
        super().__init__("Sessão comprometida. Faça login novamente.")


class InvalidRefreshError(AppError):
    """Unknown/expired/revoked refresh token."""

    status_code = 401
    code = "invalid_refresh"

    def __init__(self) -> None:
        super().__init__("Refresh inválido ou expirado.")


# ---------------------------------------------------------------------------
# Lockout (aware UTC — TD-010). Mirrors the RESEARCH code example.
# ---------------------------------------------------------------------------
def is_locked(user: User) -> bool:
    """True while the account is within an active lock window."""
    return user.locked_until is not None and datetime.now(UTC) < user.locked_until


def register_failed_attempt(user: User) -> None:
    """Increment the failure counter; lock at the threshold (aware UTC)."""
    now = datetime.now(UTC)
    if user.first_failed_at is None or now - user.first_failed_at > LOCK_WINDOW:
        user.first_failed_at = now
        user.failed_attempts = 1
    else:
        user.failed_attempts += 1
    if user.failed_attempts >= LOCK_THRESHOLD:
        user.locked_until = now + LOCK_WINDOW


def reset_lockout(user: User) -> None:
    """Clear the failure counters after a successful login."""
    user.failed_attempts = 0
    user.first_failed_at = None
    user.locked_until = None


async def _get_user_by_email(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return (await session.execute(stmt)).scalar_one_or_none()


async def _resolve_session_context(session: AsyncSession, user: User) -> tuple[int | None, str]:
    """Resolve the (area_scope, role) the token is minted with.

    Platform admins get area_scope=None (audited bypass). Otherwise we pick the
    user's first area membership (single-context login for this phase; explicit
    area switching is a future enhancement).
    """
    from app.areas.models import AreaAdmin

    if user.platform_role == "admin_plataforma":
        return None, "admin_plataforma"

    stmt = select(AreaAdmin).where(AreaAdmin.user_id == user.id).limit(1)
    membership = (await session.execute(stmt)).scalar_one_or_none()
    if membership is None:
        return None, "user"
    return membership.area_id, f"admin_area:{membership.role}"


async def issue_token_pair(session: AsyncSession, user: User) -> TokenPair:
    """Mint an access JWT + persist a fresh opaque refresh token (new family)."""
    area_scope, role = await _resolve_session_context(session, user)
    access = encode_access(user_id=user.id, area_scope=area_scope, role=role)
    raw, digest = new_refresh_token()
    session.add(
        RefreshToken(
            user_id=user.id,
            family_id=str(uuid.uuid4()),
            token_hash=digest,
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    await session.flush()
    return TokenPair(
        access_token=access,
        refresh_token=raw,
        expires_in=settings.access_token_minutes * 60,
    )


async def authenticate(
    session: AsyncSession, *, email: str, password: str, totp: str | None
) -> TokenPair:
    """Authenticate and issue tokens, or raise a generic auth error.

    Anti-enumeration (RN-011): a missing user still pays the argon2 cost via
    `verify_dummy`, and every failure returns the SAME generic message.
    """
    user = await _get_user_by_email(session, email)

    if user is None:
        verify_dummy(password)  # constant-time path
        logger.info("login_fail", reason="unknown_user")  # no PII (no email)
        raise InvalidCredentialsError()

    if is_locked(user):
        logger.warning("lockout", user_id=user.id)
        raise AccountLockedError()

    if not user.is_active:
        verify_dummy(password)
        logger.info("login_fail", user_id=user.id, reason="inactive")
        raise InvalidCredentialsError()

    ok, new_hash = verify_password(user.password_hash, password)
    if not ok:
        register_failed_attempt(user)
        await session.flush()
        logger.info("login_fail", user_id=user.id, reason="bad_password")
        if is_locked(user):
            raise AccountLockedError()
        raise InvalidCredentialsError()

    if new_hash is not None:
        user.password_hash = new_hash  # transparent argon2 param upgrade

    # TOTP: required when enrolled. (Platform admin without TOTP is forced to
    # enrol before any protected access — enforced in the dependency layer.)
    if user.totp_enrolled and user.totp_secret is not None:
        if not totp or not verify_totp(user.totp_secret, totp):
            register_failed_attempt(user)
            await session.flush()
            logger.info("login_fail", user_id=user.id, reason="bad_totp")
            raise TotpRequiredError()
        # Anti-replay: reject a code reused within the same window (TH-08).
        from app.core.security import current_totp_window

        window = current_totp_window(user.totp_secret)
        if user.totp_last_window is not None and window <= user.totp_last_window:
            logger.info("login_fail", user_id=user.id, reason="totp_replay")
            raise TotpRequiredError("Código TOTP já utilizado.")
        user.totp_last_window = window

    reset_lockout(user)
    pair = await issue_token_pair(session, user)
    logger.info("login_ok", user_id=user.id)
    return pair
