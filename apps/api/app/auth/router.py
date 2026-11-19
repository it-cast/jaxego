"""/v1/auth endpoints: login, refresh, logout (thin router).

The router stays thin (fastapi-production-patterns): it parses the contract,
delegates to the service, and shapes the response. The refresh token is set as
an httpOnly+Secure cookie (web) and also returned in the body (mobile Secure
Storage). Errors propagate as AppError (RFC-7807-like envelope) — no stack trace,
generic message (A05). The request body of auth is NEVER logged (RN-021).

TOTP enrolment endpoints are added in T-09 alongside the dependencies.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Annotated, Literal

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import password_reset, service
from app.auth.dependencies import CurrentUser
from app.auth.models import (
    ACTOR_AREA_ADMIN,
    ACTOR_COURIER,
    ACTOR_MERCHANT,
    ACTOR_PLATFORM_ADMIN,
    ACTOR_TEAM,
)
from app.auth.schemas import (
    ForgotPasswordBody,
    ForgotPasswordResponse,
    LoginBody,
    LogoutBody,
    MeResponse,
    RefreshBody,
    ResetPasswordBody,
    TokenPair,
    TotpEnrollResponse,
    TotpVerifyBody,
)
from app.core.config import settings
from app.core.ratelimit import SlidingWindowLimiter, _client_ip
from app.core.redis import get_redis
from app.core.security import (
    current_totp_window,
    generate_totp_secret,
    totp_provisioning_uri,
    verify_totp,
)
from app.db.session import get_session

router = APIRouter(prefix="/auth", tags=["auth"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]

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


# ---------------------------------------------------------------------------
# Esqueci minha senha (entregador, loja, equipe, admin da cidade). O admin da
# plataforma fica de fora: conta com TOTP, a senha dele não se troca por aqui.
# ---------------------------------------------------------------------------
PerfilReset = Literal["entregador", "loja", "equipe", "admin"]
_ACTOR_POR_PERFIL = {
    "entregador": ACTOR_COURIER,
    "loja": ACTOR_MERCHANT,
    "equipe": ACTOR_TEAM,
    "admin": ACTOR_AREA_ADMIN,
}

# Pedir código: 5 por IP e 3 por e-mail a cada 15 min. Confirmar: 10 por IP a cada 15 min
# (o código ainda cai sozinho após 5 erros).
forgot_ip_limiter = SlidingWindowLimiter(limit=5, window=timedelta(minutes=15))
forgot_email_limiter = SlidingWindowLimiter(limit=3, window=timedelta(minutes=15))
reset_ip_limiter = SlidingWindowLimiter(limit=10, window=timedelta(minutes=15))


@router.post("/{perfil}/esqueci-senha", response_model=ForgotPasswordResponse)
async def esqueci_senha(
    perfil: PerfilReset,
    body: ForgotPasswordBody,
    request: Request,
    session: SessionDep,
    redis: RedisDep,
) -> ForgotPasswordResponse:
    """Gera o código de troca de senha. Mesma resposta exista ou não a conta."""
    actor_type = _ACTOR_POR_PERFIL[perfil]
    forgot_ip_limiter.check(_client_ip(request), retry_after=900)
    forgot_email_limiter.check(f"{actor_type}:{body.email.lower()}", retry_after=900)
    code = await password_reset.request_code(
        session, redis, actor_type=actor_type, email=body.email
    )
    minutos = int(password_reset.CODE_TTL.total_seconds() // 60)
    if settings.reset_senha_mostrar_codigo:
        return ForgotPasswordResponse(
            message="Use o código abaixo para criar uma nova senha.",
            expires_in_minutes=minutos,
            code=code,
        )
    # Futuro: enviar `code` por e-mail aqui (só quando a conta existir).
    return ForgotPasswordResponse(
        message="Se o e-mail estiver cadastrado, enviamos um código para ele.",
        expires_in_minutes=minutos,
    )


@router.post("/{perfil}/redefinir-senha", status_code=204)
async def redefinir_senha(
    perfil: PerfilReset,
    body: ResetPasswordBody,
    request: Request,
    session: SessionDep,
    redis: RedisDep,
) -> Response:
    """Troca a senha com o código e encerra as sessões abertas da conta."""
    reset_ip_limiter.check(_client_ip(request), retry_after=900)
    await password_reset.reset_password(
        session,
        redis,
        actor_type=_ACTOR_POR_PERFIL[perfil],
        email=body.email,
        code=body.code,
        new_password=body.new_password,
    )
    await session.commit()
    return Response(status_code=204)


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
