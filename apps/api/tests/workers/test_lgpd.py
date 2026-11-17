"""LGPD jobs (Phase 14 — T-01 / REQ-048): anonymise inactive 12m + delete ephemeral 30d.

All data is SYNTHETIC (factories below) — never real PII. The 12m/30d windows are
exercised with a CONTROLLED clock (rows are stamped at explicit `updated_at`/`expires_at`
offsets), so the test does not depend on wall time beyond `datetime.now(UTC)`.

Desde dd23333 não há tabela `users`: a PII de conta vive na tabela de cada tipo (o entregador é a
própria conta) e não existem mais "cadastros abandonados" globais para apagar.

Coverage:
- inactive 12m courier/recipient → anonymised (PII tombstoned, conta desativada, anonymized_at set);
- recently-active entity → untouched;
- a courier under LEGAL retention (financial trail) → preserved;
- idempotency: a second run anonymises nothing new;
- expired refresh token swept; live token kept.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.areas.models import Area
from app.auth.models import RefreshToken
from app.couriers.models import Courier
from app.deliveries.models import Delivery, Recipient
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from app.payments.models import EscrowLedger
from app.workers.lifecycle import (
    _PII_NAME,
    _PII_TOMBSTONE,
    anonymize_inactive,
    delete_ephemeral,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.helpers import make_team

_OLD = timedelta(days=400)  # > 12 months
_RECENT = timedelta(days=10)


async def _area(s: AsyncSession) -> Area:
    area = Area(codename="padua", name="Pádua", config={})
    s.add(area)
    await s.flush()
    return area


async def _courier(
    s: AsyncSession, *, area_id: int, age: timedelta, cpf: str, email: str
) -> Courier:
    c = Courier(
        area_id=area_id,
        team_id=(await make_team(s, area_id=area_id)).id,
        password_hash="hash-sintetico",
        cpf=cpf,
        full_name="Entregador Sintético",
        phone_e164="+5522988887777",
        email=email,
        status="active",
    )
    s.add(c)
    await s.flush()
    stamp = datetime.now(UTC) - age
    c.created_at = stamp
    c.updated_at = stamp
    await s.flush()
    return c


async def _recipient(s: AsyncSession, *, area_id: int, age: timedelta) -> Recipient:
    r = Recipient(
        area_id=area_id,
        name="Destinatário Sintético",
        phone_e164="+5522977776666",
        email="dest@example.test",
        cpf_hash="deadbeef",
        deliveries_count=3,
        refusals_count=0,
    )
    s.add(r)
    await s.flush()
    stamp = datetime.now(UTC) - age
    r.created_at = stamp
    r.updated_at = stamp
    await s.flush()
    return r


@pytest.mark.asyncio
async def test_anonymizes_inactive_12m(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area = await _area(s)
        courier = await _courier(
            s, area_id=area.id, age=_OLD, cpf="11122233344", email="old@example.test"
        )
        recipient = await _recipient(s, area_id=area.id, age=_OLD)
        await s.commit()
        cid, rid = courier.id, recipient.id

    n = await anonymize_inactive({"session_factory": session_factory})
    assert n == 2

    async with session_factory() as s:
        c = await s.get(Courier, cid)
        assert c.full_name == _PII_NAME
        assert c.cpf is None
        assert c.phone_e164 == _PII_TOMBSTONE
        assert c.email == f"{_PII_TOMBSTONE}+{cid}@anonymized.invalid"
        # A conta do entregador não loga mais
        assert c.password_hash is None
        assert c.is_active is False
        assert c.anonymized_at is not None
        r = await s.get(Recipient, rid)
        assert r.name == _PII_NAME
        assert r.cpf_hash == _PII_TOMBSTONE
        assert r.email is None
        assert r.anonymized_at is not None
        # Statistical aggregate preserved.
        assert r.deliveries_count == 3
        # An audit row was appended per entity.
        from app.audit.models import AuditLog

        audits = (
            (await s.execute(select(AuditLog).where(AuditLog.action.like("lgpd.anonymize.%"))))
            .scalars()
            .all()
        )
        assert len(audits) == 2


@pytest.mark.asyncio
async def test_recent_entity_untouched(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area = await _area(s)
        courier = await _courier(
            s, area_id=area.id, age=_RECENT, cpf="55566677788", email="fresh@example.test"
        )
        await s.commit()
        cid = courier.id

    n = await anonymize_inactive({"session_factory": session_factory})
    assert n == 0

    async with session_factory() as s:
        c = await s.get(Courier, cid)
        assert c.full_name == "Entregador Sintético"
        assert c.anonymized_at is None


@pytest.mark.asyncio
async def test_legal_retention_preserved(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """A courier with a financial trail is NEVER anonymised, even if old (D-02)."""
    async with session_factory() as s:
        area = await _area(s)
        courier = await _courier(
            s, area_id=area.id, age=_OLD, cpf="99988877766", email="paid@example.test"
        )
        nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
        merchant = Merchant(
            area_id=area.id,
            account_type="cnpj",
            document="11222333000181",
            trade_name="Loja",
            category="restaurante",
            phone_e164="+5522999991111",
            email="loja@example.test",
            status="active",
        )
        s.add_all([nbhd, merchant])
        await s.flush()
        delivery = Delivery(
            area_id=area.id,
            merchant_id=merchant.id,
            courier_id=courier.id,
            state="FINALIZADA",
            dispatch_mode="direct",
            payment_method="card",
            proof_method="photo",
            pickup_address="a",
            dropoff_address="b",
            dropoff_neighborhood_id=nbhd.id,
            fee_cents=0,
            items_quantity=1,
            public_token="LEGALRET0000000000000000AA",
            origin="manual",
        )
        s.add(delivery)
        await s.flush()
        # A financial trail tied to the courier (legal/fiscal retention — D-02).
        s.add(
            EscrowLedger(
                area_id=area.id,
                delivery_id=delivery.id,
                courier_id=courier.id,
                amount_cents=1100,
                state="HELD",
            )
        )
        await s.commit()
        cid = courier.id

    n = await anonymize_inactive({"session_factory": session_factory})
    assert n == 0

    async with session_factory() as s:
        c = await s.get(Courier, cid)
        assert c.full_name == "Entregador Sintético"
        assert c.anonymized_at is None
        assert c.is_active is True


@pytest.mark.asyncio
async def test_anonymize_idempotent(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area = await _area(s)
        await _courier(s, area_id=area.id, age=_OLD, cpf="12312312312", email="idem@example.test")
        await _recipient(s, area_id=area.id, age=_OLD)
        await s.commit()

    assert await anonymize_inactive({"session_factory": session_factory}) == 2
    # A second run finds nothing new — anonymised rows are skipped.
    assert await anonymize_inactive({"session_factory": session_factory}) == 0


@pytest.mark.asyncio
async def test_delete_ephemeral_expired_refresh_token(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        s.add(
            RefreshToken(
                actor_type="courier",
                actor_id=1,
                family_id="fam-1",
                token_hash="a" * 64,
                expires_at=datetime.now(UTC) - timedelta(days=40),
            )
        )
        s.add(
            RefreshToken(
                actor_type="courier",
                actor_id=1,
                family_id="fam-2",
                token_hash="b" * 64,
                expires_at=datetime.now(UTC) + timedelta(days=10),
            )
        )
        await s.commit()

    assert await delete_ephemeral({"session_factory": session_factory}) == 1

    async with session_factory() as s:
        remaining = (await s.execute(select(func.count()).select_from(RefreshToken))).scalar_one()
        assert remaining == 1  # only the live token survives
