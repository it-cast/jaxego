"""F-01 signup flow exceptions E1–E4 (REQ-008), driven against STUB adapters.

These tests exercise `MerchantService.signup` directly with injected stub
adapters (no network). They assert the four exception branches and the happy
Free path.
"""

from __future__ import annotations

import time

import pytest

from app.integrations.receita_stub import ReceitaStubAdapter
from app.merchants import service
from app.merchants.schemas import MerchantSignupBody
from app.plans.service import seed_plans_if_missing
from tests.helpers import Seed

# A valid numeric CNPJ (check-digit valid) used across the happy paths.
VALID_CNPJ = "11222333000181"
VALID_CPF = "39053344705"
SIGNUP_BASE = {
    "account_type": "cnpj",
    "document": VALID_CNPJ,
    "trade_name": "Loja do Bairro",
    "category": "comercio",
    "phone_e164": "+5522999991234",
    "email": "loja@example.com",
    "password": "correct-horse-staple-10",
    "consent": True,
}


def _body(**overrides: object) -> MerchantSignupBody:
    data = {**SIGNUP_BASE, **overrides}
    return MerchantSignupBody.model_validate(data)


@pytest.fixture
async def with_plans(db_session) -> None:
    await seed_plans_if_missing(db_session)
    await db_session.commit()


@pytest.mark.asyncio
async def test_free_path_activates(db_session, seed: Seed, with_plans, geocoding_stub_padua) -> None:
    """Happy path: CNPJ ativa + Free plan → merchant active."""
    result = await service.signup(
        db_session,
        body=_body(),
        receita=ReceitaStubAdapter(scenario="ativa"),
        geocoding=geocoding_stub_padua,
    )
    assert result.status == "active"
    assert result.next_step in {"confirm", "done"}


@pytest.mark.asyncio
async def test_cnpj_inativo_bloqueia(
    db_session, seed: Seed, with_plans, geocoding_stub_padua
) -> None:
    """E1 — CNPJ inativo na Receita → cadastro bloqueado."""
    with pytest.raises(service.CnpjInativoError):
        await service.signup(
            db_session,
            body=_body(),
            receita=ReceitaStubAdapter(scenario="inativa"),
            geocoding=geocoding_stub_padua,
        )


@pytest.mark.asyncio
async def test_colisao_anti_enumeracao(
    db_session, seed: Seed, with_plans, geocoding_stub_padua
) -> None:
    """E2 — colisão de CNPJ/telefone/e-mail → mensagem única + tempo ~constante."""
    # First signup succeeds.
    await service.signup(
        db_session,
        body=_body(),
        receita=ReceitaStubAdapter(scenario="ativa"),
        geocoding=geocoding_stub_padua,
    )

    # Collide on CNPJ.
    t0 = time.perf_counter()
    with pytest.raises(service.DuplicateAccountError) as e_cnpj:
        await service.signup(
            db_session,
            body=_body(email="outra@example.com", phone_e164="+5522988887777"),
            receita=ReceitaStubAdapter(scenario="ativa"),
            geocoding=geocoding_stub_padua,
        )
    dt_cnpj = time.perf_counter() - t0

    # Collide on e-mail (different CNPJ).
    t0 = time.perf_counter()
    with pytest.raises(service.DuplicateAccountError) as e_email:
        await service.signup(
            db_session,
            body=_body(document="11444777000161", phone_e164="+5522977776666"),
            receita=ReceitaStubAdapter(scenario="ativa"),
            geocoding=geocoding_stub_padua,
        )
    dt_email = time.perf_counter() - t0

    # Same generic message — never reveals which field collided (RN-011).
    assert str(e_cnpj.value) == str(e_email.value)
    assert "esse dado" in str(e_cnpj.value).lower()
    # Roughly constant time (both pay the dummy-hash cost). Generous bound to
    # avoid flakiness; the point is neither path short-circuits.
    assert abs(dt_cnpj - dt_email) < 0.5


@pytest.mark.asyncio
async def test_pagamento_falha_vira_free(
    db_session, seed: Seed, with_plans, geocoding_stub_padua
) -> None:
    """E3 — plano pago escolhido → merchant em pending_payment, usando Free."""
    result = await service.signup(
        db_session,
        body=_body(plan_code="profissional"),
        receita=ReceitaStubAdapter(scenario="ativa"),
        geocoding=geocoding_stub_padua,
    )
    assert result.status == "pending_payment"
    # Free subscription is active even while payment is pending.
    assert result.active_plan_code == "free"


@pytest.mark.asyncio
async def test_receita_down_pending_validation(
    db_session, seed: Seed, with_plans, geocoding_stub_padua
) -> None:
    """E4 — Receita fora do ar → pending_validation + job de retry enfileirado."""
    result = await service.signup(
        db_session,
        body=_body(),
        receita=ReceitaStubAdapter(scenario="down"),
        geocoding=geocoding_stub_padua,
    )
    assert result.status == "pending_validation"
    assert result.revalidation_enqueued is True


@pytest.mark.asyncio
async def test_sem_area_estado_vazio(
    db_session, seed: Seed, with_plans, geocoding_stub_fora
) -> None:
    """Endereço fora de área → AreaNotCoveredError (estado vazio)."""
    with pytest.raises(service.AreaNotCoveredError):
        await service.signup(
            db_session,
            body=_body(),
            receita=ReceitaStubAdapter(scenario="ativa"),
            geocoding=geocoding_stub_fora,
        )
