"""Append-only trigger on delivery_state_transitions (TH-02 / RN-012 / D-04).

MySQL-only: the integrity authority is the trigger (`SIGNAL SQLSTATE '45000'`,
errno 1644). Any UPDATE/DELETE on a transition row is rejected by the database.
This mirrors the audit_log acceptance test of Phase 2. Run live:

    cd apps/api && uv run pytest -m mysql tests/deliveries/test_append_only.py
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

pytestmark = pytest.mark.mysql

MYSQL_URL = os.getenv(
    "TEST_MYSQL_URL",
    "mysql+aiomysql://jaxego:jaxego@127.0.0.1:3306/jaxego",
)


@pytest_asyncio.fixture
async def mysql_session():
    engine = create_async_engine(MYSQL_URL, echo=False)
    sm = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sm() as s:
        yield s
    await engine.dispose()


async def _seed_one_transition(s) -> int:
    """Insert a minimal area + delivery + transition row; return the transition id.

    Assumes migration 0006 (deliveries/transitions/recipients) is applied.
    """
    await s.execute(text("INSERT INTO areas (codename, name, config, created_at, updated_at) "
                         "VALUES ('t_padua', 'T', '{}', NOW(6), NOW(6))"))
    area_id = (await s.execute(text("SELECT id FROM areas WHERE codename='t_padua'"))).scalar_one()
    # Minimal delivery (most columns nullable / defaulted for the trigger test).
    await s.execute(
        text(
            "INSERT INTO deliveries (area_id, merchant_id, state, dispatch_mode, "
            "payment_method, proof_method, public_token, created_at, updated_at) "
            "VALUES (:a, 1, 'CRIADA', 'direct', 'direct', 'photo', :tok, NOW(6), NOW(6))"
        ),
        {"a": area_id, "tok": "TESTTOKEN0000000000000001"},
    )
    delivery_id = (await s.execute(text("SELECT LAST_INSERT_ID()"))).scalar_one()
    await s.execute(
        text(
            "INSERT INTO delivery_state_transitions (area_id, delivery_id, from_state, "
            "to_state, created_at) VALUES (:a, :d, NULL, 'CRIADA', NOW(6))"
        ),
        {"a": area_id, "d": delivery_id},
    )
    tid = (await s.execute(text("SELECT LAST_INSERT_ID()"))).scalar_one()
    await s.commit()
    return tid


@pytest.mark.asyncio
async def test_update_transition_rejected(mysql_session) -> None:
    tid = await _seed_one_transition(mysql_session)
    with pytest.raises(OperationalError) as exc:
        await mysql_session.execute(
            text("UPDATE delivery_state_transitions SET to_state='ACEITA' WHERE id=:i"),
            {"i": tid},
        )
        await mysql_session.commit()
    assert "1644" in str(exc.value) or "append-only" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_delete_transition_rejected(mysql_session) -> None:
    tid = await _seed_one_transition(mysql_session)
    with pytest.raises(OperationalError) as exc:
        await mysql_session.execute(
            text("DELETE FROM delivery_state_transitions WHERE id=:i"), {"i": tid}
        )
        await mysql_session.commit()
    assert "1644" in str(exc.value) or "append-only" in str(exc.value).lower()
