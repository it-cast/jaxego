"""Pessimistic lock on transition (TH-01 / LOW-1): two concurrent transitions serialize.

MySQL-only: `SELECT ... FOR UPDATE` makes two simultaneous transitions serialize.
The second transaction re-reads the row AFTER the first commits and either applies
a still-valid transition or raises InvalidTransitionError (422) if the state
already moved. Run live:

    cd apps/api && uv run pytest -m mysql tests/deliveries/test_concurrency.py
"""

from __future__ import annotations

import asyncio
import os

import pytest
import pytest_asyncio
from app.deliveries import service
from app.deliveries.models import Delivery
from app.deliveries.state_machine import InvalidTransitionError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

pytestmark = pytest.mark.mysql

MYSQL_URL = os.getenv(
    "TEST_MYSQL_URL",
    "mysql+aiomysql://jaxego:jaxego@127.0.0.1:3306/jaxego",
)


@pytest_asyncio.fixture
async def mysql_engine():
    engine = create_async_engine(MYSQL_URL, echo=False)
    yield engine
    await engine.dispose()


async def _seed_delivery(engine) -> tuple[int, int]:
    sm = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sm() as s:
        await s.execute(
            text(
                "INSERT INTO areas (codename, name, config, created_at, updated_at) "
                "VALUES ('c_padua', 'C', '{}', NOW(6), NOW(6))"
            )
        )
        area_id = (
            await s.execute(text("SELECT id FROM areas WHERE codename='c_padua'"))
        ).scalar_one()
        await s.execute(
            text(
                "INSERT INTO deliveries (area_id, merchant_id, state, dispatch_mode, "
                "payment_method, proof_method, public_token, created_at, updated_at) "
                "VALUES (:a, 1, 'CRIADA', 'direct', 'direct', 'photo', :tok, NOW(6), NOW(6))"
            ),
            {"a": area_id, "tok": "CONCURTOKEN000000000000001"},
        )
        did = (await s.execute(text("SELECT LAST_INSERT_ID()"))).scalar_one()
        await s.commit()
        return area_id, did


@pytest.mark.asyncio
async def test_two_concurrent_cancels_one_wins(mysql_engine) -> None:
    area_id, did = await _seed_delivery(mysql_engine)
    sm = async_sessionmaker(bind=mysql_engine, expire_on_commit=False)

    async def cancel() -> str:
        async with sm() as s:
            delivery = (
                await s.execute(select(Delivery).where(Delivery.id == did))
            ).scalar_one()
            try:
                await service.transition(
                    s,
                    delivery=delivery,
                    to_state="CANCELADA",
                    actor_id=None,
                    reason="corrida",
                    ip=None,
                )
                await s.commit()
                return "ok"
            except InvalidTransitionError:
                await s.rollback()
                return "invalid"

    results = await asyncio.gather(cancel(), cancel())
    # Exactly one transition succeeds; the other sees CANCELADA (terminal) → 422.
    assert sorted(results) == ["invalid", "ok"]
