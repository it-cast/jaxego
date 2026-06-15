"""LGPD jobs (Phase 14 — T-01 / REQ-048): anonymise inactive 12m + delete ephemeral 30d.

All data is SYNTHETIC (factories below) — never real PII. The 12m/30d windows are
exercised with a CONTROLLED clock (rows are stamped at explicit `updated_at`/`expires_at`
offsets), so the test does not depend on wall time beyond `datetime.now(UTC)`.

Coverage:
- inactive 12m courier/recipient/user → anonymised (PII tombstoned, anonymized_at set);
- recently-active entity → untouched;
- a courier/user under LEGAL retention (financial trail) → preserved;
- idempotency: a second run anonymises nothing new;
- abandoned signup >30d (inactive, no attachments) → hard-deleted;
- an attached/active user is NOT deleted; expired refresh token swept.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.areas.models import Area, AreaAdmin
from app.auth.models import RefreshToken, User
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

_OLD = timedelta(days=400)  # > 12 months
_RECENT = timedelta(days=10)


async def _area(s: AsyncSession) -> Area:
    area = Area(codename="padua", name="Pádua", config={})
    s.add(area)
    await s.flush()
    return area


async def _user(s: AsyncSession, *, email: str, age: timedelta, active: bool = True) -> User:
    u = User(
        email=email,
        name="Fulano Sintético",
        phone="+5522999990000",
        cpf=None,
        password_hash="x",
        platform_role="user",
        is_active=active,
    )
    s.add(u)
    await s.flush()
    stamp = datetime.now(UTC) - age
    u.created_at = stamp
    u.updated_at = stamp
    await s.flush()
    return u


async def _courier(
    s: AsyncSession, *, area_id: int, user_id: int, age: timedelta, cpf: str
) -> Courier:
    c = Courier(
        area_id=area_id,
        user_id=user_id,
        cpf=cpf,
        full_name="Entregador Sintético",
        phone_e164="+5522988887777",
        email="courier@example.test",
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
        u = await _user(s, email="old@example.test", age=_OLD)
        courier = await _courier(s, area_id=area.id, user_id=u.id, age=_OLD, cpf="11122233344")
        recipient = await _recipient(s, area_id=area.id, age=_OLD)
        await s.commit()
        cid, rid, uid = courier.id, recipient.id, u.id

    n = await anonymize_inactive({"session_factory": session_factory})
    assert n == 3

    async with session_factory() as s:
        c = await s.get(Courier, cid)
        assert c.full_name == _PII_NAME
        assert c.cpf == _PII_TOMBSTONE
        assert c.phone_e164 == _PII_TOMBSTONE
        assert c.anonymized_at is not None
        r = await s.get(Recipient, rid)
        assert r.name == _PII_NAME
        assert r.cpf_hash == _PII_TOMBSTONE
        assert r.email is None
        assert r.anonymized_at is not None
        # Statistical aggregate preserved.
        assert r.deliveries_count == 3
        loaded_user = await s.get(User, uid)
        assert loaded_user.name == _PII_NAME
        assert loaded_user.phone is None
        assert loaded_user.is_active is False
        assert loaded_user.anonymized_at is not None
        # An audit row was appended per entity.
        from app.audit.models import AuditLog

        audits = (
            (await s.execute(select(AuditLog).where(AuditLog.action.like("lgpd.anonymize.%"))))
            .scalars()
            .all()
        )
        assert len(audits) == 3


@pytest.mark.asyncio
async def test_recent_entity_untouched(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area = await _area(s)
        u = await _user(s, email="fresh@example.test", age=_RECENT)
        courier = await _courier(s, area_id=area.id, user_id=u.id, age=_RECENT, cpf="55566677788")
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
        u = await _user(s, email="paid@example.test", age=_OLD)
        courier = await _courier(s, area_id=area.id, user_id=u.id, age=_OLD, cpf="99988877766")
        nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
        s.add(nbhd)
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
        cid, uid = courier.id, u.id

    n = await anonymize_inactive({"session_factory": session_factory})
    assert n == 0

    async with session_factory() as s:
        c = await s.get(Courier, cid)
        assert c.full_name == "Entregador Sintético"
        assert c.anonymized_at is None
        # The user owning the financially-retained courier is preserved too.
        loaded_user = await s.get(User, uid)
        assert loaded_user.anonymized_at is None


@pytest.mark.asyncio
async def test_anonymize_idempotent(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area = await _area(s)
        u = await _user(s, email="idem@example.test", age=_OLD)
        await _courier(s, area_id=area.id, user_id=u.id, age=_OLD, cpf="12312312312")
        await _recipient(s, area_id=area.id, age=_OLD)
        await s.commit()

    assert await anonymize_inactive({"session_factory": session_factory}) == 3
    # A second run finds nothing new — anonymised rows are skipped.
    assert await anonymize_inactive({"session_factory": session_factory}) == 0


@pytest.mark.asyncio
async def test_delete_ephemeral_abandoned_signup(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """An inactive signup with no attachments older than 30 days is hard-deleted."""
    async with session_factory() as s:
        abandoned = await _user(
            s, email="abandoned@example.test", age=timedelta(days=45), active=False
        )
        await s.commit()
        aid = abandoned.id

    n = await delete_ephemeral({"session_factory": session_factory})
    assert n >= 1

    async with session_factory() as s:
        assert await s.get(User, aid) is None


@pytest.mark.asyncio
async def test_delete_ephemeral_keeps_attached_and_recent(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area = await _area(s)
        # Active user — not ephemeral.
        active = await _user(s, email="active@example.test", age=timedelta(days=60), active=True)
        # Attached (area admin) inactive user — must survive.
        attached = await _user(
            s, email="attached@example.test", age=timedelta(days=60), active=False
        )
        s.add(AreaAdmin(area_id=area.id, user_id=attached.id, role="owner"))
        # Recent inactive signup — under the 30d window, survives.
        recent = await _user(
            s, email="recentsignup@example.test", age=timedelta(days=5), active=False
        )
        await s.commit()
        ids = (active.id, attached.id, recent.id)

    await delete_ephemeral({"session_factory": session_factory})

    async with session_factory() as s:
        for uid in ids:
            assert await s.get(User, uid) is not None


@pytest.mark.asyncio
async def test_delete_ephemeral_expired_refresh_token(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        u = await _user(s, email="tokens@example.test", age=timedelta(days=1))
        s.add(
            RefreshToken(
                user_id=u.id,
                family_id="fam-1",
                token_hash="a" * 64,
                expires_at=datetime.now(UTC) - timedelta(days=40),
            )
        )
        s.add(
            RefreshToken(
                user_id=u.id,
                family_id="fam-2",
                token_hash="b" * 64,
                expires_at=datetime.now(UTC) + timedelta(days=10),
            )
        )
        await s.commit()

    await delete_ephemeral({"session_factory": session_factory})

    async with session_factory() as s:
        remaining = (await s.execute(select(func.count()).select_from(RefreshToken))).scalar_one()
        assert remaining == 1  # only the live token survives
