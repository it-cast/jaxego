"""Esqueci minha senha: código de 6 dígitos que troca a senha sem estar logado.

O código fica só no Redis (hash + tentativas + id da conta, 15 min de validade) —
nenhuma tabela nova no banco. Vale uma vez e cai depois de 5 tentativas erradas.

Hoje o código volta na resposta para a tela mostrar (`reset_senha_mostrar_codigo`).
Quando o envio por e-mail existir, o código passa a ir só por e-mail e essa opção é
desligada — o resto do fluxo não muda.

Anti-enumeração (RN-011): para e-mail que não existe a resposta é a mesma (inclusive
um código, que nunca vai funcionar). A redefinição com sucesso derruba todas as
sessões abertas da conta (revoga os refresh tokens).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import redis.asyncio as aioredis
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken
from app.auth.principals import _model_for
from app.auth.service import reset_lockout
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import hash_password

logger = structlog.get_logger("auth")

CODE_TTL = timedelta(minutes=15)
MAX_TRIES = 5
_KEY = "auth:reset_senha:{actor_type}:{email}"


class InvalidResetCodeError(AppError):
    """Código errado, vencido, já usado ou de outra conta — sempre a mesma mensagem."""

    status_code = 400
    code = "invalid_reset_code"

    def __init__(self) -> None:
        super().__init__(
            "Código inválido ou vencido. Confira o e-mail digitado ou peça um novo código."
        )


def _key(actor_type: str, email: str) -> str:
    return _KEY.format(actor_type=actor_type, email=email.strip().lower())


def _digest(code: str) -> str:
    """HMAC do código (o Redis nunca guarda o código puro)."""
    return hmac.new(settings.jwt_secret.encode(), code.encode(), hashlib.sha256).hexdigest()


async def _eligible_account(session: AsyncSession, actor_type: str, email: str) -> object | None:
    """Conta que pode trocar a senha: existe, ativa, não apagada e já tem senha."""
    model = _model_for(actor_type)
    account = (
        (await session.execute(select(model).where(model.email == email.strip())))
        .scalars()
        .first()
    )
    if account is None:
        return None
    if getattr(account, "deleted_at", None) is not None:
        return None
    if not bool(getattr(account, "is_active", True)):
        return None
    if getattr(account, "password_hash", None) is None:
        return None
    return account


async def request_code(
    session: AsyncSession, redis: aioredis.Redis, *, actor_type: str, email: str
) -> str:
    """Gera o código. Só grava no Redis se a conta existir; devolve o código sempre."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    account = await _eligible_account(session, actor_type, email)
    if account is None:
        logger.info("reset_senha_pedido", actor_type=actor_type, reason="conta_inexistente")
        return code
    key = _key(actor_type, email)
    await redis.delete(key)  # pedir de novo invalida o código anterior
    await redis.hset(key, mapping={"hash": _digest(code), "tries": 0, "id": account.id})
    await redis.expire(key, int(CODE_TTL.total_seconds()))
    logger.info("reset_senha_pedido", actor_type=actor_type, actor_id=account.id)
    return code


async def reset_password(
    session: AsyncSession,
    redis: aioredis.Redis,
    *,
    actor_type: str,
    email: str,
    code: str,
    new_password: str,
) -> None:
    """Confere o código e troca a senha; derruba as sessões abertas da conta."""
    key = _key(actor_type, email)
    data = await redis.hgetall(key)
    if not data:
        raise InvalidResetCodeError()
    if not hmac.compare_digest(data.get("hash", ""), _digest(code.strip())):
        tries = await redis.hincrby(key, "tries", 1)
        if tries >= MAX_TRIES:
            await redis.delete(key)
        logger.info("reset_senha_falha", actor_type=actor_type, reason="codigo_errado")
        raise InvalidResetCodeError()
    # Uso único: só quem apagar a chave segue (dois envios simultâneos → um vence).
    if await redis.delete(key) == 0:
        raise InvalidResetCodeError()

    account = await _eligible_account(session, actor_type, email)
    if account is None or str(account.id) != str(data.get("id")):
        raise InvalidResetCodeError()

    account.password_hash = hash_password(new_password)
    reset_lockout(account)  # quem esqueceu a senha costuma ter travado a conta tentando
    now = datetime.now(UTC)
    tokens = await session.execute(
        select(RefreshToken).where(
            RefreshToken.actor_type == actor_type,
            RefreshToken.actor_id == account.id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    for token in tokens.scalars().all():
        token.revoked_at = now
    await session.flush()
    logger.info("reset_senha_ok", actor_type=actor_type, actor_id=account.id)
