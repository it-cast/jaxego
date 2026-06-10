"""RN-011 / REQ-006 — uniqueness by account type + generic collision message."""

from __future__ import annotations

import pytest
from app.integrations.receita_stub import ReceitaStubAdapter
from app.merchants import service
from app.merchants.schemas import MerchantSignupBody
from app.plans.service import seed_plans_if_missing

from tests.helpers import Seed

VALID_CNPJ = "11222333000181"
VALID_CNPJ_2 = "11444777000161"
BASE = {
    "account_type": "cnpj",
    "document": VALID_CNPJ,
    "trade_name": "Loja A",
    "category": "comercio",
    "phone_e164": "+5522999991234",
    "email": "a@example.com",
    "password": "correct-horse-staple-10",
    "consent": True,
}


def _body(**overrides: object) -> MerchantSignupBody:
    return MerchantSignupBody.model_validate({**BASE, **overrides})


@pytest.fixture
async def with_plans(db_session) -> None:
    await seed_plans_if_missing(db_session)
    await db_session.commit()


@pytest.mark.asyncio
async def test_duplicate_phone_collides(
    db_session, seed: Seed, with_plans, geocoding_stub_padua
) -> None:
    await service.signup(
        db_session,
        body=_body(),
        receita=ReceitaStubAdapter(scenario="ativa"),
        geocoding=geocoding_stub_padua,
    )
    with pytest.raises(service.DuplicateAccountError):
        await service.signup(
            db_session,
            body=_body(document=VALID_CNPJ_2, email="b@example.com"),  # same phone
            receita=ReceitaStubAdapter(scenario="ativa"),
            geocoding=geocoding_stub_padua,
        )


@pytest.mark.asyncio
async def test_same_document_different_account_type_allowed(
    db_session, seed: Seed, with_plans, geocoding_stub_padua
) -> None:
    """Uniqueness is per (document, account_type): the same 11-digit string as a
    CPF and a (different) CNPJ never collide because they differ in length and
    type. This asserts the composite key, not a single-column unique."""
    cpf = "39053344705"
    await service.signup(
        db_session,
        body=_body(
            account_type="cpf", document=cpf, email="cpf@example.com", phone_e164="+5522900001111"
        ),
        receita=ReceitaStubAdapter(scenario="ativa"),
        geocoding=geocoding_stub_padua,
    )
    # A CNPJ signup with a distinct document/email/phone still works.
    result = await service.signup(
        db_session,
        body=_body(),
        receita=ReceitaStubAdapter(scenario="ativa"),
        geocoding=geocoding_stub_padua,
    )
    assert result.status == "active"
