"""Auth dependencies (RBAC, area scope) — composed FastAPI dependencies.

Authorisation lives ENTIRELY in dependencies, never in the route body (A01):
    get_current_user -> area_scope -> require_role(...) / require_platform_admin

- `get_current_user` decodes the access token with the pinned algorithm and
  required claims, loads the active user, binds `user_id` into the log context,
  and forces TOTP enrolment for a platform admin who has not enrolled yet (D-03).
- `area_scope` resolves the effective area from the token, validating it against
  an `area_id` path parameter: a non-platform admin reaching another area gets
  403 (D-06 / F-08 E1). A platform admin may operate cross-area (scope None).
- `require_role` / `require_platform_admin` gate by resolved role.
"""

from __future__ import annotations

from typing import Annotated

import jwt
import structlog
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.areas.service import load_memberships, resolve_role
from app.auth.models import User
from app.core.exceptions import AppError
from app.core.security import decode_access
from app.db.session import get_session

logger = structlog.get_logger("auth.deps")

SessionDep = Annotated[AsyncSession, Depends(get_session)]

PLATFORM_ADMIN_ROLE = "admin_plataforma"


class NotAuthenticatedError(AppError):
    """Missing/invalid access token (401)."""

    status_code = 401
    code = "not_authenticated"

    def __init__(self, message: str = "Não autenticado.") -> None:
        super().__init__(message)


class ForbiddenError(AppError):
    """Authenticated but not allowed (403)."""

    status_code = 403
    code = "forbidden"

    def __init__(self, message: str = "Acesso negado.") -> None:
        super().__init__(message)


class TotpEnrollmentRequiredError(AppError):
    """Platform admin must enrol TOTP before accessing protected resources."""

    status_code = 403
    code = "totp_enrollment_required"

    def __init__(self) -> None:
        super().__init__("Configuração de TOTP obrigatória antes de prosseguir.")


def _extract_bearer(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise NotAuthenticatedError()
    return token


async def get_current_user(request: Request, session: SessionDep) -> User:
    """Decode the access token, load the active user, bind log context."""
    token = _extract_bearer(request)
    try:
        claims = decode_access(token)
    except jwt.PyJWTError as exc:
        raise NotAuthenticatedError() from exc

    user = await session.get(User, int(claims["sub"]))  # type: ignore[arg-type]
    if user is None or not user.is_active:
        raise NotAuthenticatedError()

    # Populate the reserved user_id log field (no PII) — observability.
    structlog.contextvars.bind_contextvars(user_id=user.id)

    # Platform admin MUST enrol TOTP before any protected access (D-03/REQ-005).
    if user.platform_role == PLATFORM_ADMIN_ROLE and not user.totp_enrolled:
        # The enrolment endpoints themselves bypass this guard (see router).
        if not request.url.path.endswith(("/auth/totp/enroll", "/auth/totp/verify")):
            raise TotpEnrollmentRequiredError()

    # Cache the token's claimed scope for area_scope to read.
    request.state.token_area_scope = claims.get("area_scope")
    await load_memberships(session, user)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def area_scope(
    request: Request,
    user: CurrentUser,
    area_id: int | None = None,
) -> int | None:
    """Resolve the effective area scope, enforcing cross-area isolation (D-06).

    - Platform admin: returns None (may operate cross-area; the bypass is
      audited by the area router, never here silently).
    - Other roles: the token's area scope. If a path `area_id` is given and
      differs from the token scope -> 403 (no cross-area access).
    """
    token_scope: int | None = getattr(request.state, "token_area_scope", None)

    if user.platform_role == PLATFORM_ADMIN_ROLE:
        return None

    if area_id is not None and token_scope is not None and area_id != token_scope:
        logger.warning("cross_area_denied", user_id=user.id)
        raise ForbiddenError("Acesso a outra área não permitido.")

    return token_scope


AreaScopeDep = Annotated["int | None", Depends(area_scope)]


def require_role(*allowed: str):
    """Dependency factory: require the resolved role to be one of `allowed`.

    Matches an exact role or a prefix family (e.g. 'admin_area' matches
    'admin_area:owner').
    """

    async def _dep(user: CurrentUser, scope: AreaScopeDep) -> User:
        role = resolve_role(user, area_id=scope)
        base = role.split(":", 1)[0]
        if role not in allowed and base not in allowed:
            logger.warning("forbidden_role", user_id=user.id)
            raise ForbiddenError()
        return user

    return _dep


async def require_platform_admin(user: CurrentUser) -> User:
    """Separate dependency for platform-admin-only routes (A01)."""
    if user.platform_role != PLATFORM_ADMIN_ROLE:
        logger.warning("forbidden_not_platform_admin", user_id=user.id)
        raise ForbiddenError()
    return user


PlatformAdmin = Annotated[User, Depends(require_platform_admin)]
