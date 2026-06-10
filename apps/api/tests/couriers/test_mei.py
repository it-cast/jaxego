"""MEI validation (T-06 / RN-024 / E3).

An ACTIVE MEI with a compatible CNAE → mei_pending=False. An inactive MEI, an
incompatible CNAE, or a provider-down result (None) → mei_pending=True (the
courier still onboards — direct-payment only). CNPJ is never logged. Reuses the
ReceitaPort contract; a small fake drives the CNAE scenarios.
"""

from __future__ import annotations

import pytest
from app.couriers import service
from app.couriers.kyc import is_mei_compatible, normalize_cnae
from app.integrations.base import ReceitaResult

from tests.couriers.conftest import make_courier

VALID_CNPJ = "11222333000181"


class _FakeReceita:
    """Configurable Receita stub for MEI CNAE scenarios (no network)."""

    def __init__(self, result: ReceitaResult | None) -> None:
        self._result = result

    async def consultar_cnpj(self, cnpj: str) -> ReceitaResult | None:
        return self._result


def test_cnae_normalization() -> None:
    assert normalize_cnae("4930201") == "4930-2/01"
    assert normalize_cnae("4930-2/01") == "4930-2/01"


def test_is_mei_compatible_pure() -> None:
    assert is_mei_compatible("ativa", ["4930-2/01"]) is True
    assert is_mei_compatible("ativa", ["4712100"]) is False  # incompatible CNAE
    assert is_mei_compatible("inativa", ["4930-2/01"]) is False
    assert is_mei_compatible(None, []) is False


@pytest.mark.asyncio
async def test_mei_active_compatible_not_pending(db_session, courier_seed) -> None:
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    receita = _FakeReceita(ReceitaResult(situacao="ativa", cnaes=["4930-2/01"]))
    pending = await service.validate_mei(
        db_session, courier_id=courier.id, cnpj=VALID_CNPJ, receita=receita
    )
    assert pending is False
    await db_session.refresh(courier)
    assert courier.mei_pending is False
    assert courier.mei_cnpj == VALID_CNPJ


@pytest.mark.asyncio
async def test_mei_inactive_sets_pending(db_session, courier_seed) -> None:
    """E3 — an inactive MEI → mei_pending (direct-payment only)."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    receita = _FakeReceita(ReceitaResult(situacao="inativa", cnaes=["4930-2/01"]))
    pending = await service.validate_mei(
        db_session, courier_id=courier.id, cnpj=VALID_CNPJ, receita=receita
    )
    assert pending is True
    await db_session.refresh(courier)
    assert courier.mei_pending is True


@pytest.mark.asyncio
async def test_mei_incompatible_cnae_sets_pending(db_session, courier_seed) -> None:
    """E3 — an active MEI with an incompatible CNAE → mei_pending."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    receita = _FakeReceita(ReceitaResult(situacao="ativa", cnaes=["4712100"]))
    pending = await service.validate_mei(
        db_session, courier_id=courier.id, cnpj=VALID_CNPJ, receita=receita
    )
    assert pending is True


@pytest.mark.asyncio
async def test_mei_provider_down_sets_pending(db_session, courier_seed) -> None:
    """Provider down (None) → mei_pending (courier still onboards direct)."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    receita = _FakeReceita(None)
    pending = await service.validate_mei(
        db_session, courier_id=courier.id, cnpj=VALID_CNPJ, receita=receita
    )
    assert pending is True
