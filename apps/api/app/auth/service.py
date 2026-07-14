"""Auth service: login por tipo de conta, lockout (5/15min, aware UTC),
anti-enumeration, TOTP (só platform_admin), refresh issue/rotate/reuse-detection,
logout.

Não existe mais a tabela global `users`: cada tipo de acesso (courier, merchant,
team, area_admin, platform_admin) autentica na própria tabela via o endpoint de
login do seu tipo. Security invariants live here, server-side (A04). All
datetimes are aware UTC (TD-010). Login emits structured events WITHOUT PII
(RN-021). The login path spends ~constant time whether or not the account
exists (anti-enumeration, RN-011).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import (
    ACTOR_PLATFORM_ADMIN,
    RefreshToken,
)
from app.auth.principals import Actor, build_actor, load_actor, _model_for
from app.auth.schemas import MeResponse, TokenPair
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import (
    encode_access,
    hash_refresh_token,
    new_refresh_token,
    verify_dummy,
    verify_password,
    verify_totp,
)
from app.db.mixins import ensure_aware_utc

logger = structlog.get_logger("auth")

# Lockout policy — derived from ADR-005 + OWASP A04 (inviabiliza brute force sem
# punir caps lock): 5 attempts within a 15-minute sliding window per account.
LOCK_THRESHOLD = 5
LOCK_WINDOW = timedelta(minutes=15)

# Single generic message — never reveals whether the account exists (RN-011/A05).
INVALID_CREDENTIALS = "Credenciais inválidas."


class InvalidCredentialsError(AppError):
    """Generic auth failure — same message for unknown account / wrong password."""

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
# Lockout (aware UTC — TD-010) — genérico para qualquer tabela com
# CredentialsMixin (failed_attempts / first_failed_at / locked_until).
# ---------------------------------------------------------------------------
def is_locked(account: object) -> bool:
    """True while the account is within an active lock window."""
    locked_until = getattr(account, "locked_until", None)
    return locked_until is not None and datetime.now(UTC) < ensure_aware_utc(locked_until)


def register_failed_attempt(account: object) -> None:
    """Increment the failure counter; lock at the threshold (aware UTC)."""
    now = datetime.now(UTC)
    first = getattr(account, "first_failed_at", None)
    if first is None or now - ensure_aware_utc(first) > LOCK_WINDOW:
        account.first_failed_at = now
        account.failed_attempts = 1
    else:
        account.failed_attempts += 1
    if account.failed_attempts >= LOCK_THRESHOLD:
        account.locked_until = now + LOCK_WINDOW


def reset_lockout(account: object) -> None:
    """Clear the failure counters after a successful login."""
    account.failed_attempts = 0
    account.first_failed_at = None
    account.locked_until = None


# ---------------------------------------------------------------------------
# Surface / contexto do token — direto do ator (sem prioridade mágica).
# ---------------------------------------------------------------------------
def resolve_surface_for(actor: Actor) -> MeResponse:
    """MeResponse do ator — cada tipo cai SEMPRE na sua superfície."""
    if actor.type == "courier":
        return MeResponse(
            user_id=actor.id,
            surface="entregador",
            area_id=actor.area_id,
            courier_id=actor.id,
            status=actor.row.status,
        )
    if actor.type == "merchant":
        m = actor.row
        return MeResponse(
            user_id=actor.id,
            surface="loja",
            area_id=actor.area_id,
            merchant_id=actor.id,
            trade_name=m.trade_name,
            address=m.address,
            address_number=m.address_number,
            address_neighborhood=m.address_neighborhood,
            status=m.status,
        )
    if actor.type == "team":
        return MeResponse(
            user_id=actor.id, surface="equipe", area_id=actor.area_id, team_id=actor.id
        )
    if actor.type == "area_admin":
        return MeResponse(user_id=actor.id, surface="admin", area_id=actor.area_id)
    return MeResponse(user_id=actor.id, surface="plataforma")


async def issue_token_pair(
    session: AsyncSession, actor: Actor, *, family_id: str | None = None
) -> TokenPair:
    """Mint an access JWT + persist a fresh opaque refresh token.

    A new login starts a new family; a rotation passes the existing `family_id`
    so reuse-detection can revoke the whole chain (TH-03).
    """
    access = encode_access(
        actor_id=actor.id, actor_type=actor.type, area_scope=actor.area_id, role=actor.role
    )
    raw, digest = new_refresh_token()
    session.add(
        RefreshToken(
            actor_type=actor.type,
            actor_id=actor.id,
            family_id=family_id or str(uuid.uuid4()),
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
    session: AsyncSession,
    *,
    actor_type: str,
    email: str,
    password: str,
    totp: str | None = None,
) -> TokenPair:
    """Authenticate against the actor's own table and issue tokens.

    Anti-enumeration (RN-011): a missing account still pays the argon2 cost via
    `verify_dummy`, and every failure returns the SAME generic message.
    """
    model = _model_for(actor_type)
    stmt = select(model).where(model.email == email)
    account = (await session.execute(stmt)).scalars().first()

    if account is None or getattr(account, "password_hash", None) is None:
        verify_dummy(password)  # constant-time path
        logger.info("login_fail", actor_type=actor_type, reason="unknown_account")
        raise InvalidCredentialsError()

    if getattr(account, "deleted_at", None) is not None:
        verify_dummy(password)
        logger.info("login_fail", actor_type=actor_type, reason="deleted")
        raise InvalidCredentialsError()

    if is_locked(account):
        logger.warning("lockout", actor_type=actor_type, actor_id=account.id)
        raise AccountLockedError()

    if not bool(getattr(account, "is_active", True)):
        verify_dummy(password)
        logger.info("login_fail", actor_type=actor_type, actor_id=account.id, reason="inactive")
        raise InvalidCredentialsError()

    ok, new_hash = verify_password(account.password_hash, password)
    if not ok:
        register_failed_attempt(account)
        # COMMIT now: the failure counter / lock must persist even though we
        # raise (the router does not commit on the error path).
        await session.commit()
        logger.info("login_fail", actor_type=actor_type, actor_id=account.id, reason="bad_password")
        if is_locked(account):
            raise AccountLockedError()
        raise InvalidCredentialsError()

    if new_hash is not None:
        account.password_hash = new_hash  # transparent argon2 param upgrade

    # TOTP: só platform_admin tem TOTP (D-03).
    if actor_type == ACTOR_PLATFORM_ADMIN:
        if account.totp_required and account.totp_enrolled and account.totp_secret is not None:
            if not totp or not verify_totp(account.totp_secret, totp):
                register_failed_attempt(account)
                await session.commit()
                logger.info("login_fail", actor_type=actor_type, actor_id=account.id, reason="bad_totp")
                raise TotpRequiredError()
            # Anti-replay: reject a code reused within the same window (TH-08).
            from app.core.security import current_totp_window

            window = current_totp_window(account.totp_secret)
            if account.totp_last_window is not None and window <= account.totp_last_window:
                logger.info("login_fail", actor_id=account.id, reason="totp_replay")
                raise TotpRequiredError("Código TOTP já utilizado.")
            account.totp_last_window = window

    reset_lockout(account)
    actor = build_actor(actor_type, account)
    pair = await issue_token_pair(session, actor)
    logger.info("login_ok", actor_type=actor_type, actor_id=account.id)
    return pair


# ---------------------------------------------------------------------------
# Refresh rotation + reuse detection (Pattern 4, TH-02/TH-03).
# ---------------------------------------------------------------------------
async def _find_refresh(session: AsyncSession, raw: str) -> RefreshToken | None:
    digest = hash_refresh_token(raw)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == digest)
    return (await session.execute(stmt)).scalar_one_or_none()


async def _revoke_family(session: AsyncSession, family_id: str) -> None:
    """Revoke every (still-active) token in a family (reuse => compromised)."""
    now = datetime.now(UTC)
    stmt = select(RefreshToken).where(
        RefreshToken.family_id == family_id,
        RefreshToken.revoked_at.is_(None),
    )
    for token in (await session.execute(stmt)).scalars().all():
        token.revoked_at = now
    await session.flush()


async def rotate_refresh(session: AsyncSession, raw: str) -> TokenPair:
    """Validate a refresh token and rotate it, or detect reuse and revoke family.

    - Unknown / revoked / expired -> InvalidRefreshError (401).
    - Already rotated (reuse of a spent token) -> revoke the whole family +
      RefreshReuseError (401). Re-login required (TH-03).
    - Valid -> mark rotated, issue a new pair within the SAME family.
    """
    token = await _find_refresh(session, raw)
    if token is None:
        raise InvalidRefreshError()

    if token.revoked_at is not None or token.rotated_at is not None:
        # A revoked or already-rotated (spent) token reused => session
        # compromised. Revoke the whole family and COMMIT now — the revocation
        # must persist even though we raise (the router does not commit on the
        # error path). Re-login is required (TH-03).
        await _revoke_family(session, token.family_id)
        await session.commit()
        logger.warning("refresh_reuse_detected", actor_id=token.actor_id)
        raise RefreshReuseError()

    if datetime.now(UTC) >= ensure_aware_utc(token.expires_at):
        raise InvalidRefreshError()

    actor = await load_actor(session, actor_type=token.actor_type, actor_id=token.actor_id)
    if actor is None:
        raise InvalidRefreshError()

    token.rotated_at = datetime.now(UTC)
    pair = await issue_token_pair(session, actor, family_id=token.family_id)
    logger.info("refresh_rotated", actor_type=actor.type, actor_id=actor.id)
    return pair


async def logout(session: AsyncSession, raw: str) -> None:
    """Revoke the presented refresh token (best-effort; idempotent).

    A courier logging out is taken offline server-side (CORRECAO-253) — the
    app can't be trusted to always call "ficar offline" itself (killed,
    crashed, connection lost), so this is the one choke point every logout
    goes through regardless of client.
    """
    token = await _find_refresh(session, raw)
    if token is not None and token.revoked_at is None:
        token.revoked_at = datetime.now(UTC)
        await session.flush()
        logger.info("logout", actor_id=token.actor_id)
        if token.actor_type == "courier":
            from app.core.exceptions import NotFoundError
            from app.couriers.availability import set_availability

            try:
                await set_availability(
                    session, area_id=None, courier_id=token.actor_id, online=False
                )
            except NotFoundError:
                pass  # revocation above already succeeded; going offline is best-effort
