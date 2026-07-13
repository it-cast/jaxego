"""Auth dependencies (RBAC, area scope) — composed FastAPI dependencies.

Authorisation lives ENTIRELY in dependencies, never in the route body (A01):
    get_current_user -> area_scope -> require_role(...) / require_platform_admin

Pós-remoção da tabela `users`: o token carrega `typ` (courier|merchant|team|
area_admin|platform_admin) + `sub` (id na tabela do tipo). `get_current_user`
carrega o `Actor` da tabela certa. O guard de TOTP vale só para platform_admin.
"""

from __future__ import annotations

from typing import Annotated

import jwt
import structlog
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import ACTOR_PLATFORM_ADMIN, ACTOR_TYPES
from app.auth.principals import Actor, load_actor
from app.core.exceptions import AppError
from app.core.security import decode_access
from app.db.session import get_session

logger = structlog.get_logger("auth.deps")

SessionDep = Annotated[AsyncSession, Depends(get_session)]


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


async def get_current_user(request: Request, session: SessionDep) -> Actor:
    """Decode the access token, load the actor from its own table, bind context."""
    token = _extract_bearer(request)
    try:
        claims = decode_access(token)
    except jwt.PyJWTError as exc:
        raise NotAuthenticatedError() from exc

    actor_type = str(claims.get("typ", ""))
    if actor_type not in ACTOR_TYPES:
        raise NotAuthenticatedError()

    actor = await load_actor(
        session, actor_type=actor_type, actor_id=int(claims["sub"])  # type: ignore[arg-type]
    )
    if actor is None:
        raise NotAuthenticatedError()

    # Populate the reserved log fields (no PII) — observability.
    structlog.contextvars.bind_contextvars(user_id=actor.id, actor_type=actor.type)

    # TOTP guard: só platform_admin tem TOTP obrigatório (D-03).
    if actor.type == ACTOR_PLATFORM_ADMIN:
        row = actor.row
        if row.totp_required and not row.totp_enrolled:
            if not request.url.path.endswith(
                ("/auth/totp/enroll", "/auth/totp/verify", "/auth/me")
            ):
                raise TotpEnrollmentRequiredError()

    # Cache the token's claimed scope for area_scope to read.
    request.state.token_area_scope = claims.get("area_scope")
    return actor


CurrentUser = Annotated[Actor, Depends(get_current_user)]


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

    if user.type == ACTOR_PLATFORM_ADMIN:
        return None

    if area_id is not None and token_scope is not None and area_id != token_scope:
        logger.warning("cross_area_denied", user_id=user.id)
        raise ForbiddenError("Acesso a outra área não permitido.")

    return token_scope


AreaScopeDep = Annotated["int | None", Depends(area_scope)]


def require_role(*allowed: str):
    """Dependency factory: require the actor's role to be one of `allowed`.

    Matches an exact role or a prefix family (e.g. 'admin_area' matches
    'admin_area:owner').
    """

    async def _dep(user: CurrentUser, scope: AreaScopeDep) -> Actor:
        role = user.role
        base = role.split(":", 1)[0]
        if role not in allowed and base not in allowed:
            logger.warning("forbidden_role", user_id=user.id, actor_type=user.type)
            raise ForbiddenError()
        return user

    return _dep


async def require_platform_admin(user: CurrentUser) -> Actor:
    """Separate dependency for platform-admin-only routes (A01)."""
    if user.type != ACTOR_PLATFORM_ADMIN:
        logger.warning("forbidden_not_platform_admin", user_id=user.id)
        raise ForbiddenError()
    return user


PlatformAdmin = Annotated[Actor, Depends(require_platform_admin)]
