"""Importable test helpers (dataclasses + login/bearer utilities).

Kept out of conftest so test modules can `from tests.helpers import ...`
(conftest is a pytest plugin, not a normal importable module).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.areas.models import Area, AreaAdmin
from app.auth.models import PlatformAdmin
from httpx import AsyncClient


@dataclass
class Seed:
    """Seeded entities for isolation/RBAC tests."""

    area_a: Area
    area_b: Area
    admin_a: AreaAdmin
    admin_b: AreaAdmin
    platform_admin: PlatformAdmin
    password: str


# Desde dd23333 o login é por tipo de conta (/v1/auth/<tipo>/login); não existe mais /v1/auth/login
LOGIN_PATHS = {
    "admin": "/v1/auth/admin/login",
    "plataforma": "/v1/auth/plataforma/login",
    "loja": "/v1/auth/loja/login",
    "entregador": "/v1/auth/entregador/login",
    "equipe": "/v1/auth/equipe/login",
}


async def login(
    client: AsyncClient,
    email: str,
    password: str,
    totp: str | None = None,
    actor: str | None = None,
) -> dict:
    """Login e devolve o JSON (falha se não for 200).

    Com `actor`, usa o endpoint daquele tipo de conta; sem ele, tenta os tipos em ordem (os
    testes antigos só passavam e-mail e senha) e devolve o primeiro que aceitar.
    """
    payload: dict = {"email": email, "password": password}
    if totp is not None:
        payload["totp"] = totp
    paths = [LOGIN_PATHS[actor]] if actor else list(LOGIN_PATHS.values())
    resp = None
    for path in paths:
        resp = await client.post(path, json=payload)
        if resp.status_code == 200:
            return resp.json()
    assert resp is not None
    resp.raise_for_status()
    raise AssertionError(f"login falhou: {resp.status_code} {resp.text}")


def bearer(token: str) -> dict[str, str]:
    """Authorization header for an access token."""
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Contas por ator (desde dd23333 não existe `users`): cada entidade tem e-mail/senha próprios.
# ---------------------------------------------------------------------------
SENHA_TESTE = "correct-horse-staple-10"


async def make_team(session, *, area_id: int, name: str = "Equipe Teste"):
    """Equipe da área (Courier.team_id é obrigatório). Reaproveita a primeira equipe da área."""
    from app.teams.models import Team
    from sqlalchemy import select

    existente = (
        (await session.execute(select(Team).where(Team.area_id == area_id).order_by(Team.id)))
        .scalars()
        .first()
    )
    if existente is not None:
        return existente
    from app.core.security import hash_password

    team = Team(
        area_id=area_id,
        name=name,
        email=f"equipe{area_id}@example.com",
        password_hash=hash_password(SENHA_TESTE),
    )
    session.add(team)
    await session.flush()
    return team
