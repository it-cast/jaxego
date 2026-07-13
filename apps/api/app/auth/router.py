"""/v1/auth endpoints: login, refresh, logout (thin router).

The router stays thin (fastapi-production-patterns): it parses the contract,
delegates to the service, and shapes the response. The refresh token is set as
an httpOnly+Secure cookie (web) and also returned in the body (mobile Secure
Storage). Errors propagate as AppError (RFC-7807-like envelope) — no stack trace,
generic message (A05). The request body of auth is NEVER logged (RN-021).

TOTP enrolment endpoints are added in T-09 alongside the dependencies.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.dependencies import CurrentUser
from app.auth.models import (
    ACTOR_AREA_ADMIN,
    ACTOR_COURIER,
    ACTOR_MERCHANT,
    ACTOR_PLATFORM_ADMIN,
    ACTOR_TEAM,
)
from app.auth.schemas import (
    LoginBody,
    LogoutBody,
    MeResponse,
    RefreshBody,
    TokenPair,
    TotpEnrollResponse,
    TotpVerifyBody,
)
from app.core.config import settings
from app.core.security import (
    current_totp_window,
    generate_totp_secret,
    totp_provisioning_uri,
    verify_totp,
)
from app.db.session import get_session

router = APIRouter(prefix="/auth", tags=["auth"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]

REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, raw: str) -> None:
    """Set the refresh token as an httpOnly+Secure cookie (web clients)."""
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw,
        httponly=True,
        secure=settings.environment != "dev",
        samesite="strict",
        max_age=settings.refresh_token_days * 24 * 3600,
        path="/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE, path="/v1/auth")


async def _login(
    body: LoginBody, response: Response, session: AsyncSession, *, actor_type: str
) -> TokenPair:
    pair = await service.authenticate(
        session, actor_type=actor_type, email=body.email, password=body.password, totp=body.totp
    )
    await session.commit()
    _set_refresh_cookie(response, pair.refresh_token)
    return pair


@router.post("/entregador/login", response_model=TokenPair)
async def login_entregador(body: LoginBody, response: Response, session: SessionDep) -> TokenPair:
    """Login do entregador — autentica na tabela couriers."""
    return await _login(body, response, session, actor_type=ACTOR_COURIER)


@router.post("/loja/login", response_model=TokenPair)
async def login_loja(body: LoginBody, response: Response, session: SessionDep) -> TokenPair:
    """Login da loja — autentica na tabela merchants."""
    return await _login(body, response, session, actor_type=ACTOR_MERCHANT)


@router.post("/equipe/login", response_model=TokenPair)
async def login_equipe(body: LoginBody, response: Response, session: SessionDep) -> TokenPair:
    """Login da equipe — autentica na tabela teams."""
    return await _login(body, response, session, actor_type=ACTOR_TEAM)


@router.post("/admin/login", response_model=TokenPair)
async def login_admin_area(body: LoginBody, response: Response, session: SessionDep) -> TokenPair:
    """Login do admin da cidade — autentica na tabela area_admins."""
    return await _login(body, response, session, actor_type=ACTOR_AREA_ADMIN)


@router.post("/plataforma/login", response_model=TokenPair)
async def login_plataforma(body: LoginBody, response: Response, session: SessionDep) -> TokenPair:
    """Login do admin do sistema — autentica na tabela platform_admins (TOTP)."""
    return await _login(body, response, session, actor_type=ACTOR_PLATFORM_ADMIN)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    body: RefreshBody,
    request: Request,
    response: Response,
    session: SessionDep,
) -> TokenPair:
    """Rotate a refresh token (cookie or body) and issue a new pair."""
    raw = body.refresh_token or request.cookies.get(REFRESH_COOKIE)
    if not raw:
        raise service.InvalidRefreshError()
    pair = await service.rotate_refresh(session, raw)
    await session.commit()
    _set_refresh_cookie(response, pair.refresh_token)
    return pair


@router.post("/logout", status_code=204)
async def logout(
    body: LogoutBody,
    request: Request,
    response: Response,
    session: SessionDep,
) -> Response:
    """Revoke the presented refresh token and clear the cookie."""
    raw = body.refresh_token or request.cookies.get(REFRESH_COOKIE)
    if raw:
        await service.logout(session, raw)
        await session.commit()
    _clear_refresh_cookie(response)
    response.status_code = 204
    return response


@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser) -> MeResponse:
    """Resolved identity + surface for the authenticated user (R0.4).

    The SPA calls this right after login to route the user to the correct shell
    (entregador / loja / equipe / admin / plataforma) and on app boot to restore
    context. O tipo já vem do token — cada conta cai sempre na sua superfície.
    """
    return service.resolve_surface_for(user)


@router.post("/totp/enroll", response_model=TotpEnrollResponse)
async def totp_enroll(user: CurrentUser, session: SessionDep) -> TotpEnrollResponse:
    """Generate a TOTP secret + provisioning URI (shown ONCE; never re-fetched).

    Só platform_admin tem TOTP (D-03). Enrolment is confirmed by /totp/verify
    with a code from the authenticator app.
    """
    from app.core.exceptions import ValidationAppError

    if user.type != ACTOR_PLATFORM_ADMIN:
        raise ValidationAppError("TOTP disponível apenas para admin da plataforma.")
    admin = user.row
    if admin.totp_enrolled:
        raise ValidationAppError("TOTP já configurado nesta conta.")
    secret = generate_totp_secret()
    admin.totp_secret = secret
    await session.commit()
    uri = totp_provisioning_uri(secret, account_name=admin.email)
    return TotpEnrollResponse(provisioning_uri=uri, secret=secret)


@router.post("/totp/verify", status_code=204)
async def totp_verify(
    body: TotpVerifyBody,
    user: CurrentUser,
    response: Response,
    session: SessionDep,
) -> Response:
    """Confirm TOTP enrolment with a code; flips totp_enrolled/required on."""
    from app.core.exceptions import ValidationAppError

    if user.type != ACTOR_PLATFORM_ADMIN:
        raise ValidationAppError("TOTP disponível apenas para admin da plataforma.")
    admin = user.row
    if admin.totp_secret is None or not verify_totp(admin.totp_secret, body.code):
        raise service.TotpRequiredError("Código TOTP inválido.")
    admin.totp_enrolled = True
    admin.totp_required = True
    admin.totp_last_window = current_totp_window(admin.totp_secret)
    await session.commit()
    response.status_code = 204
    return response
