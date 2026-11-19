"""Esqueci minha senha: código no Redis, uso único, anti-enumeração, derruba sessões."""

from __future__ import annotations

import fakeredis.aioredis
import pytest
import pytest_asyncio
from app.auth import router as auth_router
from app.auth.models import RefreshToken
from app.core.config import settings
from app.core.redis import get_redis
from app.db.session import get_session
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from tests.helpers import login

NOVA = "senha-nova-bem-longa"


@pytest.fixture(autouse=True)
def _limpa_limitadores():
    for lim in (
        auth_router.forgot_ip_limiter,
        auth_router.forgot_email_limiter,
        auth_router.reset_ip_limiter,
    ):
        lim.reset()
    yield


@pytest_asyncio.fixture
async def redis():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest_asyncio.fixture
async def cliente(session_factory, redis):
    from app.main import create_app

    async def _sessao():
        async with session_factory() as s:
            yield s

    async def _redis():
        yield redis

    app = create_app()
    app.dependency_overrides[get_session] = _sessao
    app.dependency_overrides[get_redis] = _redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac


async def _pedir(cliente, email, perfil="admin"):
    r = await cliente.post(f"/v1/auth/{perfil}/esqueci-senha", json={"email": email})
    assert r.status_code == 200, r.text
    return r.json()


async def _redefinir(cliente, email, code, senha=NOVA, perfil="admin"):
    return await cliente.post(
        f"/v1/auth/{perfil}/redefinir-senha",
        json={"email": email, "code": code, "new_password": senha},
    )


@pytest.mark.asyncio
async def test_troca_a_senha_com_o_codigo_e_derruba_sessoes(cliente, seed, session_factory):
    email = seed.admin_a.email
    await login(cliente, email, seed.password, actor="admin")

    dados = await _pedir(cliente, email)
    assert dados["code"] and len(dados["code"]) == 6
    assert dados["expires_in_minutes"] == 15

    r = await _redefinir(cliente, email, dados["code"])
    assert r.status_code == 204, r.text

    # senha antiga não entra mais, a nova entra
    velha = await cliente.post(
        "/v1/auth/admin/login", json={"email": email, "password": seed.password}
    )
    assert velha.status_code == 401
    await login(cliente, email, NOVA, actor="admin")

    # a sessão aberta antes da troca foi revogada
    async with session_factory() as s:
        tokens = (
            await s.execute(
                select(RefreshToken).where(RefreshToken.actor_id == seed.admin_a.id)
            )
        ).scalars().all()
    assert sum(1 for t in tokens if t.revoked_at is not None) >= 1


@pytest.mark.asyncio
async def test_codigo_vale_uma_vez(cliente, seed):
    email = seed.admin_a.email
    code = (await _pedir(cliente, email))["code"]
    assert (await _redefinir(cliente, email, code)).status_code == 204
    r = await _redefinir(cliente, email, code, senha="outra-senha-qualquer")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_reset_code"


@pytest.mark.asyncio
async def test_pedir_de_novo_invalida_o_codigo_anterior(cliente, seed):
    email = seed.admin_a.email
    primeiro = (await _pedir(cliente, email))["code"]
    segundo = (await _pedir(cliente, email))["code"]
    if primeiro != segundo:
        assert (await _redefinir(cliente, email, primeiro)).status_code == 400
    assert (await _redefinir(cliente, email, segundo)).status_code == 204


@pytest.mark.asyncio
async def test_codigo_cai_depois_de_5_erros(cliente, seed):
    email = seed.admin_a.email
    code = (await _pedir(cliente, email))["code"]
    errado = "000000" if code != "000000" else "111111"
    for _ in range(5):
        assert (await _redefinir(cliente, email, errado)).status_code == 400
    assert (await _redefinir(cliente, email, code)).status_code == 400


@pytest.mark.asyncio
async def test_email_inexistente_tem_a_mesma_resposta(cliente, seed, redis):
    dados = await _pedir(cliente, "ninguem@example.com")
    assert dados["code"] and len(dados["code"]) == 6
    assert await redis.keys("auth:reset_senha:*") == []
    r = await _redefinir(cliente, "ninguem@example.com", dados["code"])
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_codigo_de_um_perfil_nao_serve_em_outro(cliente, seed):
    email = seed.admin_a.email
    code = (await _pedir(cliente, email))["code"]
    assert (await _redefinir(cliente, email, code, perfil="loja")).status_code == 400


@pytest.mark.asyncio
async def test_plataforma_fica_de_fora(cliente, seed):
    r = await cliente.post(
        "/v1/auth/plataforma/esqueci-senha", json={"email": seed.platform_admin.email}
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_senha_curta_e_recusada(cliente, seed):
    email = seed.admin_a.email
    code = (await _pedir(cliente, email))["code"]
    assert (await _redefinir(cliente, email, code, senha="curta")).status_code == 422


@pytest.mark.asyncio
async def test_sem_mostrar_codigo_nao_devolve_o_codigo(cliente, seed, monkeypatch):
    monkeypatch.setattr(settings, "reset_senha_mostrar_codigo", False)
    dados = await _pedir(cliente, seed.admin_a.email)
    assert dados["code"] is None


@pytest.mark.asyncio
async def test_limite_de_pedidos_por_email(cliente, seed):
    for _ in range(3):
        await _pedir(cliente, seed.admin_a.email)
    r = await cliente.post(
        "/v1/auth/admin/esqueci-senha", json={"email": seed.admin_a.email}
    )
    assert r.status_code == 429
