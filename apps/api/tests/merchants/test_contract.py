"""API contract tests (T-02): extra='forbid', GET /v1/plans from SEED, consent."""

from __future__ import annotations

import pytest
from app.plans.service import seed_plans_if_missing
from httpx import AsyncClient


@pytest.fixture
async def seeded_plans(session_factory) -> None:
    async with session_factory() as s:
        await seed_plans_if_missing(s)
        await s.commit()


@pytest.mark.asyncio
async def test_signup_rejects_extra_field(auth_client: AsyncClient) -> None:
    resp = await auth_client.post(
        "/v1/merchants/signup",
        json={
            "account_type": "cnpj",
            "document": "11222333000181",
            "trade_name": "Loja",
            "category": "comercio",
            "phone_e164": "+5522999991234",
            "email": "a@example.com",
            "password": "correct-horse-staple-10",
            "consent": True,
            "is_admin": True,  # extra field — must be rejected (A03)
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_requires_consent(auth_client: AsyncClient) -> None:
    resp = await auth_client.post(
        "/v1/merchants/signup",
        json={
            "account_type": "cnpj",
            "document": "11222333000181",
            "trade_name": "Loja",
            "category": "comercio",
            "phone_e164": "+5522999991234",
            "email": "a@example.com",
            "password": "correct-horse-staple-10",
            "consent": False,  # LGPD: must be explicitly true
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_plans_returns_seed_values(auth_client: AsyncClient, seeded_plans) -> None:
    resp = await auth_client.get("/v1/plans")
    assert resp.status_code == 200
    plans = resp.json()
    assert len(plans) == 4
    by_code = {p["codename"]: p for p in plans}
    assert by_code["free"]["is_free"] is True
    assert by_code["free"]["preco_cents"] == 0
    # Values come from the seed (DRV-009) — not hardcoded in the response model.
    assert by_code["sem_limite"]["is_unlimited"] is True


@pytest.mark.asyncio
async def test_interest_accepts_with_consent(auth_client: AsyncClient) -> None:
    resp = await auth_client.post(
        "/v1/interest",
        json={"email": "quero@example.com", "cidade": "Itaperuna", "consent": True},
    )
    assert resp.status_code == 202
