"""Revalidation job — retry windows 6/6/12/24h in aware UTC (TD-010, REQ-008)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.integrations.receita_stub import ReceitaStubAdapter
from app.merchants import service
from app.merchants.schemas import MerchantSignupBody
from app.plans.service import seed_plans_if_missing
from app.workers.revalidate import RETRY_WINDOWS_HOURS, next_retry_delay

from tests.helpers import Seed

BASE = {
    "area_id": 1,
    "account_type": "cnpj",
    "document": "11222333000181",
    "trade_name": "Loja",
    "category": "comercio",
    "phone_e164": "+5522999991234",
    "email": "loja@example.com",
    "password": "correct-horse-staple-10",
    "consent": True,
}


def test_retry_windows_are_6_6_12_24() -> None:
    assert RETRY_WINDOWS_HOURS == (6, 6, 12, 24)


def test_next_retry_delay_progression() -> None:
    assert next_retry_delay(0).total_seconds() == 6 * 3600
    assert next_retry_delay(1).total_seconds() == 6 * 3600
    assert next_retry_delay(2).total_seconds() == 12 * 3600
    assert next_retry_delay(3).total_seconds() == 24 * 3600


def test_next_retry_delay_exhausted_returns_none() -> None:
    assert next_retry_delay(len(RETRY_WINDOWS_HOURS)) is None


@pytest.mark.asyncio
async def test_revalidate_promotes_pending_to_active(db_session, seed: Seed) -> None:
    from app.workers.revalidate import revalidate_merchant

    await seed_plans_if_missing(db_session)
    await db_session.commit()

    # Create a pending_validation merchant (Receita was down).
    result = await service.signup(
        db_session,
        body=MerchantSignupBody.model_validate(BASE),
        receita=ReceitaStubAdapter(scenario="down"),
        geocoding=_StubGeoPadua(),
    )
    await db_session.commit()
    assert result.status == "pending_validation"

    # Receita comes back "ativa" → revalidation promotes to active (aware UTC).
    promoted = await revalidate_merchant(
        db_session,
        merchant_id=result.merchant_id,
        receita=ReceitaStubAdapter(scenario="ativa"),
        now=datetime.now(UTC),
    )
    assert promoted is True


class _StubGeoPadua:
    """Inline geocoder that always lands in Pádua (avoids fixture wiring here)."""

    async def geocode(self, address: str):  # noqa: ANN001, ANN201
        from app.integrations.base import GeocodeResult

        return GeocodeResult(lat=-21.541, lng=-42.043)
