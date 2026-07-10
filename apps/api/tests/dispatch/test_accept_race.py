"""THE race test (REQ-024 — critério nº 1): 2 simultaneous accepts → 1 wins.

MySQL + real Redis only. Two coroutines accept the SAME offer at the same instant;
exactly ONE wins (delivery → ACEITA) and the OTHER is rejected WITHOUT penalty
(F-05 E3 — no cancellation, no extra transition for the loser).

We assert the *invariant*, not one specific exception type. The defense in depth
(D-05) is real and the loser can legitimately land on ANY layer depending on the
interleaving: (a) `NotOfferTargetError` (404) — the winner already cleared
`offer:{id}` in Redis before the loser's A01 target check ran; (b) the redis `Lock`
not acquired in time, OR (c) `state != CRIADA` after the `SELECT ... FOR UPDATE`
(Phase 7 `transition()`), OR (d) the CRIADA→ACEITA machine rejecting — all three of
which surface as `OfferAlreadyTakenError` (409). EVERY one of these is a
"rejected without penalty" outcome (F-05 E3); the production logic is correct as-is.

The invariant that ALWAYS holds for ANY interleaving:
    * exactly 1 success (Delivery in ACEITA) and exactly 1 rejection exception;
    * the delivery is ACEITA, bound to exactly 1 courier, `cancelled_at` is NULL;
    * exactly 1 CRIADA→ACEITA row in `delivery_state_transitions`.

Run live:
    cd apps/api && uv run pytest -m mysql tests/dispatch/test_accept_race.py

Connection lifecycle mirrors tests/deliveries/test_concurrency.py: a dedicated
NullPool engine created+disposed inside the test loop (Windows aiomysql), and a
real Redis client from settings (the offer/lock need true Redis semantics — LOW-2).
The seeded rows are cleaned up for idempotent re-runs.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from app.areas.models import Area
from app.auth.models import User
from app.core.config import settings
from app.core.security import hash_password
from app.couriers.models import Courier
from app.deliveries.models import Delivery, DeliveryStateTransition, Recipient
from app.deliveries.state_machine import InvalidTransitionError
from app.dispatch import offer_state
from app.dispatch.exceptions import NotOfferTargetError, OfferAlreadyTakenError
from app.dispatch.service import accept_offer
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

pytestmark = pytest.mark.mysql


@pytest_asyncio.fixture
async def mysql_engine() -> AsyncIterator[AsyncEngine]:
    """Dedicated async engine created and disposed within the test event loop."""
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(settings.database_url, echo=False, poolclass=NullPool)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def real_redis() -> AsyncIterator[aioredis.Redis]:
    """A real Redis client (from settings) — the Lock needs true semantics (LOW-2)."""
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


async def _seed(engine: AsyncEngine) -> tuple[int, int, int, int]:
    """Seed area + store + 2 couriers + CRIADA delivery. Returns ids."""
    codename = f"race-test-{uuid.uuid4().hex[:12]}"
    sm = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    async with sm() as s:
        area = Area(codename=codename, name="Race Test", config={})
        s.add(area)
        await s.flush()

        suffix = uuid.uuid4().int % 10_000_000
        u1 = User(
            email=f"c1-{suffix}@example.com",
            name="C1",
            password_hash=hash_password("correct-horse-staple-10"),
            platform_role="user",
        )
        u2 = User(
            email=f"c2-{suffix}@example.com",
            name="C2",
            password_hash=hash_password("correct-horse-staple-10"),
            platform_role="user",
        )
        s.add_all([u1, u2])
        await s.flush()

        merchant = Merchant(
            area_id=area.id,
            account_type="cnpj",
            document=f"{suffix:014d}",
            trade_name="Loja Race",
            category="restaurante",
            phone_e164=f"+5522{suffix:09d}",
            email=f"race-{suffix}@example.com",
            status="active",
        )
        s.add(merchant)
        await s.flush()

        nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
        s.add(nbhd)
        await s.flush()

        c1 = Courier(
            area_id=area.id,
            user_id=u1.id,
            cpf=f"{suffix:011d}",
            full_name="C1",
            phone_e164=f"+5522{suffix:09d}",
            email=f"c1-{suffix}@example.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
            is_online=True,
        )
        c2 = Courier(
            area_id=area.id,
            user_id=u2.id,
            cpf=f"{(suffix + 1):011d}",
            full_name="C2",
            phone_e164=f"+5523{suffix:09d}",
            email=f"c2-{suffix}@example.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
            is_online=True,
        )
        s.add_all([c1, c2])
        await s.flush()

        recipient = Recipient(
            area_id=area.id,
            name="Cliente",
            phone_e164="+5522988887777",
            deliveries_count=0,
            refusals_count=0,
        )
        s.add(recipient)
        await s.flush()

        delivery = Delivery(
            area_id=area.id,
            merchant_id=merchant.id,
            courier_id=None,
            recipient_id=recipient.id,
            state="CRIADA",
            dispatch_mode="direct",
            payment_method="direct",
            proof_method="photo",
            pickup_address="Rua A, 1",
            dropoff_address="Rua B, 2",
            dropoff_neighborhood_id=nbhd.id,
            distance_m=1000,
            fee_cents=0,
            items_quantity=1,
            public_token=uuid.uuid4().hex[:26].upper(),
            origin="manual",
        )
        s.add(delivery)
        await s.flush()
        ids = (area.id, delivery.id, c1.id, c2.id)
        await s.commit()
        return ids


async def _cleanup(engine: AsyncEngine, *, area_id: int) -> None:
    sm = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    async with sm() as s:
        await s.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in (
            "deliveries",
            "recipients",
            "couriers",
            "merchants",
            "neighborhoods_catalog",
        ):
            await s.execute(text(f"DELETE FROM {table} WHERE area_id = :a"), {"a": area_id})
        await s.execute(text("DELETE FROM areas WHERE id = :a"), {"a": area_id})
        await s.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        await s.commit()


# The set of rejections that are ALL "rejected without penalty" (F-05 E3). The loser
# can legitimately land on any of the D-05 defense layers depending on interleaving:
#   * NotOfferTargetError (404)  — winner already cleared offer:{id} before A01 check
#   * OfferAlreadyTakenError (409) — lock not acquired / state != CRIADA / machine reject
#   * InvalidTransitionError (422) — the CRIADA→ACEITA machine itself rejected
# None of them is a cancellation; none costs the loser anything.
_REJECTION_EXCEPTIONS = (
    NotOfferTargetError,
    OfferAlreadyTakenError,
    InvalidTransitionError,
)


@pytest.mark.asyncio
async def test_two_concurrent_accepts_one_wins(
    mysql_engine: AsyncEngine, real_redis: aioredis.Redis
) -> None:
    area_id, did, c1, c2 = await _seed(mysql_engine)
    sm = async_sessionmaker(bind=mysql_engine, expire_on_commit=False, autoflush=False)

    # A barrier maximises overlap so the two accepts truly contend; the invariant
    # below holds for ANY interleaving regardless of who reaches each layer first.
    barrier = asyncio.Barrier(2)

    async def accept(courier_id: int) -> Delivery:
        """Each contender uses its OWN session/connection — the real race needs it.

        Each (re)asserts itself as the current offer target just before the race so
        BOTH pass the A01 check at open; the Lock + FOR UPDATE then pick ONE winner.
        Returns the ACEITA Delivery on success; raises on rejection (caught by gather).
        """
        async with sm() as s:
            await offer_state.open_offer(
                real_redis, delivery_id=did, courier_id=courier_id, timeout_s=30
            )
            await barrier.wait()
            try:
                delivery = await accept_offer(
                    s,
                    real_redis,
                    area_id=area_id,
                    delivery_id=did,
                    courier_id=courier_id,
                    actor_user_id=None,
                    ip=None,
                )
                await s.commit()
                return delivery
            except Exception:
                await s.rollback()
                raise

    try:
        results = await asyncio.gather(accept(c1), accept(c2), return_exceptions=True)

        successes = [r for r in results if isinstance(r, Delivery)]
        failures = [r for r in results if isinstance(r, BaseException)]

        # INVARIANT 1 — exactly one wins, exactly one is rejected. NEVER 2 successes.
        assert len(successes) == 1, (
            f"expected exactly 1 winner, got {len(successes)} "
            f"(double-accept bug?) — results={results!r}"
        )
        assert len(failures) == 1, (
            f"expected exactly 1 rejection, got {len(failures)} — results={results!r}"
        )

        # The winning return value is the ACEITA delivery bound to a real courier.
        winner = successes[0]
        assert winner.state == "ACEITA"
        assert winner.courier_id in (c1, c2)

        # INVARIANT 2 — the loser is a rejection WITHOUT penalty (any D-05 layer).
        loser_exc = failures[0]
        assert isinstance(loser_exc, _REJECTION_EXCEPTIONS), (
            f"loser raised an unexpected exception type: {loser_exc!r}"
        )

        # INVARIANT 3 — DB truth: ACEITA, exactly 1 courier, NO cancellation (F-05 E3),
        # and exactly ONE CRIADA→ACEITA transition row (no extra transition for loser).
        async with sm() as s:
            delivery = await s.get(Delivery, did)
            assert delivery is not None
            assert delivery.state == "ACEITA"
            assert delivery.courier_id in (c1, c2)
            assert delivery.courier_id == winner.courier_id
            assert delivery.cancelled_at is None  # no penalty for the loser

            accepted_transitions = (
                await s.execute(
                    select(func.count())
                    .select_from(DeliveryStateTransition)
                    .where(
                        DeliveryStateTransition.delivery_id == did,
                        DeliveryStateTransition.from_state == "CRIADA",
                        DeliveryStateTransition.to_state == "ACEITA",
                    )
                )
            ).scalar_one()
            assert accepted_transitions == 1, (
                f"expected exactly 1 CRIADA→ACEITA transition, got "
                f"{accepted_transitions} (loser left a transition?)"
            )
    finally:
        await offer_state.close_offer(real_redis, did)
        await offer_state.clear_candidates(real_redis, did)
        await _cleanup(mysql_engine, area_id=area_id)
