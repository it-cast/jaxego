"""Escrow ledger: hold/release/freeze. Release only FINALIZADA+24h, no dispute.

TH-G: release only via the cron, atomic, idempotent (only if still HELD). RN-006:
24h aware-UTC after FINALIZADA without an open dispute. A dispute within 24h freezes
ONLY that delivery (F-07 E4); the others release.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_hold_then_release_after_24h(payments_seed, session_factory) -> None:
    from app.payments import escrow
    from app.payments.models import EscrowLedger

    async with session_factory() as s:
        hold = await escrow.hold(
            s,
            area_id=payments_seed.area_a_id,
            delivery_id=1,
            courier_id=payments_seed.courier_id,
            amount_cents=1000,
        )
        await s.commit()
        assert hold.state == "HELD"

    # finalized 25h ago, no dispute → release_escrow releases it.
    cutoff_past = datetime.now(UTC) - timedelta(hours=25)
    async with session_factory() as s:
        led = await s.get(EscrowLedger, hold.id)
        led.finalized_at = cutoff_past
        await s.commit()

    released = await escrow.release_ready(session_factory)
    assert released == 1

    async with session_factory() as s:
        led = await s.get(EscrowLedger, hold.id)
        assert led.state == "RELEASED"


@pytest.mark.asyncio
async def test_release_skips_recent(payments_seed, session_factory) -> None:
    from app.payments import escrow
    from app.payments.models import EscrowLedger

    async with session_factory() as s:
        hold = await escrow.hold(
            s,
            area_id=payments_seed.area_a_id,
            delivery_id=2,
            courier_id=payments_seed.courier_id,
            amount_cents=1000,
        )
        await s.commit()
    async with session_factory() as s:
        led = await s.get(EscrowLedger, hold.id)
        led.finalized_at = datetime.now(UTC) - timedelta(hours=1)  # only 1h ago
        await s.commit()

    released = await escrow.release_ready(session_factory)
    assert released == 0


@pytest.mark.asyncio
async def test_release_is_idempotent(payments_seed, session_factory) -> None:
    from app.payments import escrow
    from app.payments.models import EscrowLedger

    async with session_factory() as s:
        hold = await escrow.hold(
            s,
            area_id=payments_seed.area_a_id,
            delivery_id=3,
            courier_id=payments_seed.courier_id,
            amount_cents=500,
        )
        await s.commit()
    async with session_factory() as s:
        led = await s.get(EscrowLedger, hold.id)
        led.finalized_at = datetime.now(UTC) - timedelta(hours=25)
        await s.commit()

    assert await escrow.release_ready(session_factory) == 1
    # Second run finds nothing still HELD → 0 (no double credit).
    assert await escrow.release_ready(session_factory) == 0


@pytest.mark.asyncio
async def test_freeze_isolates_one_delivery(payments_seed, session_factory) -> None:
    from app.payments import escrow
    from app.payments.models import EscrowLedger

    async with session_factory() as s:
        a = await escrow.hold(
            s,
            area_id=payments_seed.area_a_id,
            delivery_id=4,
            courier_id=payments_seed.courier_id,
            amount_cents=1000,
        )
        b = await escrow.hold(
            s,
            area_id=payments_seed.area_a_id,
            delivery_id=5,
            courier_id=payments_seed.courier_id,
            amount_cents=1000,
        )
        await s.commit()
    async with session_factory() as s:
        for led_id in (a.id, b.id):
            led = await s.get(EscrowLedger, led_id)
            led.finalized_at = datetime.now(UTC) - timedelta(hours=25)
        # Freeze delivery 4 only.
        await escrow.freeze(s, escrow_id=a.id)
        await s.commit()

    released = await escrow.release_ready(session_factory)
    assert released == 1  # only b released; a is FROZEN
    async with session_factory() as s:
        assert (await s.get(EscrowLedger, a.id)).state == "FROZEN"
        assert (await s.get(EscrowLedger, b.id)).state == "RELEASED"
