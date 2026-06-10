"""Pessimistic lock on transition (TH-01 / LOW-1): two concurrent cancels serialize.

MySQL-only: `SELECT ... FOR UPDATE` (in `service.transition`) makes two simultaneous
cancels serialize. The second transaction re-reads the row AFTER the first commits
and raises InvalidTransitionError (422) because the delivery already moved to the
terminal CANCELADA state. Run live:

    cd apps/api && uv run pytest -m mysql tests/deliveries/test_concurrency.py

Connection lifecycle: a DEDICATED async engine is built and disposed inside the
test's own event loop (`mysql_engine` fixture, NullPool + `await engine.dispose()`
in teardown), exactly like `tests/neighborhoods/test_spatial.py`. The process-wide
`app.db.session.engine` pools aiomysql connections created outside any test loop;
when a function-scoped loop closes, the pooled `aiomysql.Connection.__del__` fires
against an already-closed loop and raises `RuntimeError: Event loop is closed`,
which pytest escalates into a spurious FAILED on Windows. Per-test dispose within
the loop avoids that entirely.

Seed: the delivery is built through the REAL `Delivery(...)` ORM model so EVERY
NOT NULL column is supplied (a raw partial INSERT trips
`(1364, "Field 'pickup_address' doesn't have a default value")`), and the two
cancels exercise the REAL `service.transition` (the FOR UPDATE lock). The seeded
area/neighborhood/delivery are torn down for idempotency.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.core.config import settings
from app.deliveries import service
from app.deliveries.models import Delivery
from app.deliveries.state_machine import InvalidTransitionError
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

pytestmark = pytest.mark.mysql


@pytest_asyncio.fixture
async def mysql_engine() -> AsyncIterator[AsyncEngine]:
    """A dedicated async engine created and disposed within the test event loop.

    NullPool keeps no connection alive between checkouts, and the explicit
    `await engine.dispose()` in teardown closes everything inside this loop, so no
    aiomysql connection is ever finalized against a closed loop on Windows.
    """
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(settings.database_url, echo=False, poolclass=NullPool)
    try:
        yield engine
    finally:
        await engine.dispose()


async def _seed_delivery(engine: AsyncEngine) -> tuple[int, int]:
    """Seed area + neighborhood + a VALID delivery (every NOT NULL column).

    Returns (area_id, delivery_id). Built via the real `Delivery(...)` ORM model.
    """
    codename = f"concur-test-{uuid.uuid4().hex[:12]}"
    sm = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    async with sm() as s:
        area = Area(codename=codename, name="Concurrency Test", config={})
        s.add(area)
        await s.flush()

        nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
        s.add(nbhd)
        await s.flush()

        suffix = uuid.uuid4().int % 10_000_000
        merchant = Merchant(
            area_id=area.id,
            account_type="cnpj",
            document=f"{suffix:014d}",
            trade_name="Loja Concurrency Test",
            category="restaurante",
            phone_e164=f"+5522{suffix:09d}",
            email=f"concur-{suffix}@example.com",
            status="active",
        )
        s.add(merchant)
        await s.flush()

        delivery = Delivery(
            area_id=area.id,
            merchant_id=merchant.id,
            recipient_id=None,
            state="CRIADA",
            dispatch_mode="direct",
            payment_method="direct",
            proof_method="photo",
            pickup_address="Rua do Comércio, 100",
            dropoff_address="Rua das Flores, 200",
            dropoff_neighborhood_id=nbhd.id,
            fee_cents=0,
            items_quantity=1,
            public_token=uuid.uuid4().hex[:26].upper(),
            origin="manual",
        )
        s.add(delivery)
        await s.flush()
        did = delivery.id
        await s.commit()
        return area.id, did


async def _cleanup(engine: AsyncEngine, *, area_id: int) -> None:
    """Remove the seeded delivery/neighborhood/area so re-runs start clean.

    The transition rows are append-only (the trigger blocks DELETE), so the
    delivery cannot be removed while a transition references it. FK checks are
    disabled for this teardown session only (idempotency cleanup, not a production
    path); the append-only transition rows are intentionally left in place.
    """
    sm = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    async with sm() as s:
        await s.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        await s.execute(text("DELETE FROM deliveries WHERE area_id = :a"), {"a": area_id})
        await s.execute(text("DELETE FROM merchants WHERE area_id = :a"), {"a": area_id})
        await s.execute(
            text("DELETE FROM neighborhoods_catalog WHERE area_id = :a"), {"a": area_id}
        )
        await s.execute(text("DELETE FROM areas WHERE id = :a"), {"a": area_id})
        await s.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        await s.commit()


@pytest.mark.asyncio
async def test_two_concurrent_cancels_one_wins(mysql_engine: AsyncEngine) -> None:
    area_id, did = await _seed_delivery(mysql_engine)
    sm = async_sessionmaker(bind=mysql_engine, expire_on_commit=False, autoflush=False)

    # Both coroutines rendezvous at the barrier, then call the REAL
    # `service.transition` simultaneously so they contend on the SAME
    # `SELECT ... FOR UPDATE` row lock (the only delivery read of each transaction).
    #
    # Why no prior non-locking SELECT: under InnoDB REPEATABLE READ a plain SELECT
    # would pin the transaction's consistent snapshot at CRIADA, and the loser's
    # later FOR UPDATE would then re-read that STALE CRIADA even after the winner
    # committed CANCELADA — masking the lock. Each real cancel request is its own
    # fresh transaction whose FIRST delivery read can be the locking read, so here
    # we pass a stub carrying only `id` (all `transition` needs to locate the row)
    # and let transition's FOR UPDATE be that first read. The loser then blocks,
    # re-reads the committed terminal CANCELADA, and the state machine rejects it
    # (InvalidTransitionError → 422).
    #
    # The winner holds the row lock through a short delay BEFORE commit so the loser
    # is provably parked on the FOR UPDATE until CANCELADA is durable; the delay
    # only fires for whoever won the lock (the loser never reaches it). This makes
    # the pessimistic-lock assertion deterministic instead of timing-dependent.
    barrier = asyncio.Barrier(2)

    async def cancel() -> str:
        async with sm() as s:
            stub = Delivery()
            stub.id = did  # transition() re-reads FOR UPDATE by id; only id is used.
            await barrier.wait()
            try:
                await service.transition(
                    s,
                    delivery=stub,
                    to_state="CANCELADA",
                    actor_id=None,
                    reason="corrida",
                    ip=None,
                )
                await asyncio.sleep(0.25)
                await s.commit()
                return "ok"
            except InvalidTransitionError:
                await s.rollback()
                return "invalid"

    try:
        results = await asyncio.gather(cancel(), cancel())
        # Exactly one transition succeeds; the other sees CANCELADA (terminal) → 422.
        assert sorted(results) == ["invalid", "ok"]
    finally:
        await _cleanup(mysql_engine, area_id=area_id)
