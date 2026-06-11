"""Score composition, level mapping and idempotent snapshot (T-02 / REQ-020 / ADR-013)."""

from __future__ import annotations

from datetime import date

import pytest
import pytest_asyncio
from app.couriers.models import Courier
from app.scores.service import (
    CourierSignals,
    build_snapshot,
    compose,
    level_for,
    seed_weights_if_missing,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers import Seed


@pytest_asyncio.fixture
async def courier(db_session: AsyncSession, seed: Seed) -> Courier:
    c = Courier(
        area_id=seed.area_a.id,
        user_id=seed.admin_a.id,
        cpf="11111111111",
        full_name="Entregador Teste",
        phone_e164="+5522999999999",
        email="courier@example.com",
        kyc_level="simples",
        status="active",
        vehicle_type="moto",
    )
    db_session.add(c)
    await db_session.flush()
    return c


@pytest.mark.asyncio
async def test_level_mapping_bands() -> None:
    assert level_for(95.0) == "diamante"
    assert level_for(80.0) == "ouro"
    assert level_for(60.0) == "prata"
    assert level_for(40.0) == "bronze"
    assert level_for(10.0) == "probation"
    assert level_for(0.0) == "probation"


@pytest.mark.asyncio
async def test_compose_sums_weighted_contributions() -> None:
    weights = {
        "acceptance_rate": 0.25,
        "punctuality": 0.25,
        "proof_ok": 0.20,
        "low_cancellation": 0.15,
        "ratings": 0.15,
    }
    # All raw = 1.0 → total 100; breakdown lists every component (ADR-013 explainability).
    total, components = compose(CourierSignals(1.0, 1.0, 1.0, 1.0, 1.0), weights)
    assert total == pytest.approx(100.0)
    assert len(components) == 5
    assert {c["component"] for c in components} == set(weights)
    for c in components:
        assert {"component", "raw", "weight", "contribution"} <= set(c)


@pytest.mark.asyncio
async def test_snapshot_is_idempotent_per_day(
    db_session: AsyncSession, courier: Courier
) -> None:
    """Running the snapshot twice on the same day updates ONE row (1/dia/courier)."""
    await seed_weights_if_missing(db_session)
    signals = CourierSignals(0.8, 0.8, 0.8, 1.0, 0.75)
    day = date(2026, 6, 11)

    s1 = await build_snapshot(
        db_session,
        courier_id=courier.id,
        area_id=courier.area_id,
        signals=signals,
        snapshot_date=day,
    )
    # Re-run same day (e.g. job retried) — must update, not duplicate.
    s2 = await build_snapshot(
        db_session,
        courier_id=courier.id,
        area_id=courier.area_id,
        signals=signals,
        snapshot_date=day,
    )

    assert s1.id == s2.id
    count = (
        await db_session.execute(
            select(func.count())
            .select_from(s1.__class__)
            .where(s1.__class__.courier_id == courier.id)
        )
    ).scalar_one()
    assert count == 1
    assert s2.level in ("probation", "bronze", "prata", "ouro", "diamante")


@pytest.mark.asyncio
async def test_snapshot_level_reflects_signals(
    db_session: AsyncSession, courier: Courier
) -> None:
    await seed_weights_if_missing(db_session)
    high = await build_snapshot(
        db_session,
        courier_id=courier.id,
        area_id=courier.area_id,
        signals=CourierSignals(1.0, 1.0, 1.0, 1.0, 1.0),
        snapshot_date=date(2026, 6, 10),
    )
    assert high.level == "diamante"
    assert float(high.total_score) == pytest.approx(100.0)
