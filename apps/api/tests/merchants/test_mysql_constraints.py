"""Merchants schema acceptance — LIVE MySQL 8 (migration 0003 applied).

Marked `@pytest.mark.mysql`: requires a real MySQL 8 with migrations upgraded to
`0003_merchants_plans`. Asserts the RN-011 uniqueness constraints actually exist
and bite at the database level (the SQLite suite asserts the service behaviour;
this asserts the DDL is the real authority). Run live with:

    uv run pytest -m mysql tests/merchants/test_mysql_constraints.py -x

Skipped by default in dev (`-m "not mysql"`).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from app.core.config import settings
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

pytestmark = pytest.mark.mysql


@pytest_asyncio.fixture
async def mysql_engine() -> AsyncIterator[AsyncEngine]:
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(settings.database_url, echo=False, poolclass=NullPool)
    try:
        yield engine
    finally:
        await engine.dispose()


async def _ensure_area(engine: AsyncEngine) -> int:
    async with engine.begin() as conn:
        row = (
            await conn.execute(text("SELECT id FROM areas WHERE codename = 'padua' LIMIT 1"))
        ).first()
        if row is not None:
            return int(row[0])
        result = await conn.execute(
            text(
                "INSERT INTO areas (codename, name, config, created_at, updated_at) "
                "VALUES ('padua', 'Pádua', '{}', UTC_TIMESTAMP(6), UTC_TIMESTAMP(6))"
            )
        )
        return int(result.lastrowid)  # type: ignore[union-attr]


async def _insert_merchant(engine: AsyncEngine, area_id: int, *, doc: str, phone: str, email: str):
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO merchants (area_id, account_type, document, trade_name, category, "
                "phone_e164, email, status, receita_validated, revalidation_attempts, "
                "created_at, updated_at) VALUES (:area, 'cnpj', :doc, 'Loja', 'comercio', "
                ":phone, :email, 'active', 1, 0, UTC_TIMESTAMP(6), UTC_TIMESTAMP(6))"
            ),
            {"area": area_id, "doc": doc, "phone": phone, "email": email},
        )


async def _delete_merchants_by_document(engine: AsyncEngine, doc: str) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM merchants WHERE document = :doc"), {"doc": doc})


@pytest.mark.asyncio
async def test_duplicate_document_violates_unique(mysql_engine: AsyncEngine) -> None:
    # Self-isolate: the CNPJ 11222333000181 is a shared fixture document inserted by
    # several other @mysql merchant tests in the same session against this shared DB.
    # Clean it before AND after so this test is idempotent regardless of run order
    # (otherwise a leftover row makes the FIRST insert below blow up instead of the
    # intended duplicate, breaking the suite on re-runs / cross-test pollution).
    doc = "11222333000181"
    await _delete_merchants_by_document(mysql_engine, doc)
    try:
        area_id = await _ensure_area(mysql_engine)
        await _insert_merchant(
            mysql_engine, area_id, doc=doc, phone="+5522900000001", email="m1@ex.com"
        )
        with pytest.raises(IntegrityError):
            await _insert_merchant(
                mysql_engine,
                area_id,
                doc=doc,  # same (account_type, document) — RN-011
                phone="+5522900000002",
                email="m2@ex.com",
            )
    finally:
        await _delete_merchants_by_document(mysql_engine, doc)
