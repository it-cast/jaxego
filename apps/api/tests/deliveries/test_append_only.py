"""Append-only trigger on delivery_state_transitions (TH-02 / RN-012 / D-04).

MySQL-only: the integrity authority is the trigger (`SIGNAL SQLSTATE '45000'`,
errno 1644). Any UPDATE/DELETE on a transition row is rejected by the database.
This mirrors the audit_log acceptance test of Phase 2 (`test_audit_append_only.py`).
Run live:

    cd apps/api && uv run pytest -m mysql tests/deliveries/test_append_only.py

Connection lifecycle: a DEDICATED async engine is built and disposed inside the
test's own event loop (`mysql_engine` fixture, NullPool + `await engine.dispose()`
in teardown), exactly like `tests/neighborhoods/test_spatial.py`. The process-wide
`app.db.session.engine` pools aiomysql connections created outside any test loop;
when a function-scoped loop closes, the pooled `aiomysql.Connection.__del__` fires
against an already-closed loop and raises `RuntimeError: Event loop is closed`,
which pytest escalates into a spurious FAILED on Windows. Per-test dispose within
the loop avoids that entirely.

Seed: the delivery is built through the REAL `Delivery(...)` ORM model so EVERY
NOT NULL column (pickup_address, dropoff_address, dropoff_neighborhood_id, …) is
supplied — a raw partial INSERT trips `(1364, "Field 'pickup_address' doesn't have
a default value")`. Each test seeds a unique-codename area + neighborhood +
delivery + one transition row, asserts, then tears everything down for idempotency.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.core.config import settings
from app.deliveries.models import Delivery, DeliveryStateTransition
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
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


@pytest_asyncio.fixture
async def mysql_session(
    mysql_engine: AsyncEngine,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Session factory bound to the live MySQL engine (real `mysql` dialect)."""
    yield async_sessionmaker(bind=mysql_engine, expire_on_commit=False, autoflush=False)


async def _seed_one_transition(
    factory: async_sessionmaker[AsyncSession],
) -> tuple[int, int]:
    """Seed area + neighborhood + a VALID delivery + one transition row.

    Returns (area_id, transition_id). The delivery is built via the real
    `Delivery(...)` ORM model so every NOT NULL column is populated.
    """
    codename = f"append-test-{uuid.uuid4().hex[:12]}"
    async with factory() as s:
        area = Area(codename=codename, name="Append Test", config={})
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
            trade_name="Loja Append Test",
            category="restaurante",
            phone_e164=f"+5522{suffix:09d}",
            email=f"append-{suffix}@example.com",
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

        transition = DeliveryStateTransition(
            area_id=area.id,
            delivery_id=delivery.id,
            from_state=None,
            to_state="CRIADA",
            created_at=datetime.now(UTC),
        )
        s.add(transition)
        await s.flush()
        tid = transition.id
        await s.commit()
        return area.id, tid


async def _cleanup(factory: async_sessionmaker[AsyncSession], *, area_id: int) -> None:
    """Remove the seeded delivery/neighborhood/area so re-runs start clean.

    The transition rows are append-only (the trigger blocks DELETE) and reference
    the delivery/area with `ondelete=RESTRICT`, so the rows cannot be removed and
    the parents cannot be deleted while a transition points at them. FK checks are
    therefore disabled for this teardown session only (idempotency cleanup, not a
    production path); the append-only transition rows are intentionally left behind.
    """
    async with factory() as s:
        # Append-only trigger blocks DELETE on transitions; FK checks would block
        # deleting the delivery while a transition references it. Disable FK checks
        # for this teardown session only (idempotency cleanup, not production path).
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
async def test_update_transition_rejected(
    mysql_session: async_sessionmaker[AsyncSession],
) -> None:
    area_id, tid = await _seed_one_transition(mysql_session)
    try:
        with pytest.raises(OperationalError) as exc:
            async with mysql_session() as s:
                await s.execute(
                    text("UPDATE delivery_state_transitions SET to_state='ACEITA' WHERE id=:i"),
                    {"i": tid},
                )
                await s.commit()
        msg = str(exc.value)
        assert "1644" in msg or "45000" in msg or "append-only" in msg.lower()
    finally:
        await _cleanup(mysql_session, area_id=area_id)


@pytest.mark.asyncio
async def test_delete_transition_rejected(
    mysql_session: async_sessionmaker[AsyncSession],
) -> None:
    area_id, tid = await _seed_one_transition(mysql_session)
    try:
        with pytest.raises(OperationalError) as exc:
            async with mysql_session() as s:
                await s.execute(
                    text("DELETE FROM delivery_state_transitions WHERE id=:i"), {"i": tid}
                )
                await s.commit()
        msg = str(exc.value)
        assert "1644" in msg or "45000" in msg or "append-only" in msg.lower()
    finally:
        await _cleanup(mysql_session, area_id=area_id)
