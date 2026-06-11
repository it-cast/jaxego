"""Internal 24h escrow ledger (Phase 10 — RN-006 / TH-G). aware-UTC (TD-010).

A delivery's corrida is HELD on charge (`hold`) and released into the courier's
withdrawable balance only via the cron (`release_ready`), and only when the delivery is
FINALIZADA (Phase 9 sets `finalized_at`) AND 24h have passed AND there is no open dispute
(checked at finalisation; a dispute within the 24h FREEZES only that hold — F-07 E4). The
release is atomic (ledger transition + balance credit in one commit) and idempotent (only
a still-HELD row releases — TH-G/TH-J).

`[ASSUMIDO A5]`: the escrow window is the Jaxegô domain's 24h, INDEPENDENT of the PSP's
repasse schedule (DEC-003). The withdrawable balance itself (payout) is Phase 11; here we
only mark the ledger RELEASED.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.exceptions import NotFoundError
from app.payments import repo
from app.payments.models import EscrowLedger

logger = structlog.get_logger("payments.escrow")

RELEASE_AFTER = timedelta(hours=24)


async def hold(
    session: AsyncSession,
    *,
    area_id: int,
    delivery_id: int,
    courier_id: int,
    amount_cents: int,
) -> EscrowLedger:
    """Create a HELD escrow entry for a delivery's corrida (on charge). Caller commits."""
    entry = EscrowLedger(
        area_id=area_id,
        delivery_id=delivery_id,
        courier_id=courier_id,
        amount_cents=amount_cents,
        state="HELD",
    )
    session.add(entry)
    await session.flush()
    return entry


async def freeze(session: AsyncSession, *, escrow_id: int) -> EscrowLedger:
    """Freeze a single hold (a dispute opened within the 24h — F-07 E4). Caller commits."""
    entry = await session.get(EscrowLedger, escrow_id)
    if entry is None:
        raise NotFoundError("Lançamento de escrow não encontrado.")
    if entry.state == "HELD":
        entry.state = "FROZEN"
        await session.flush()
    return entry


async def release_ready(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Cron: release HELD holds FINALIZADA+24h, atomic + idempotent. Returns count.

    Only rows still HELD with `finalized_at <= now-24h` release; a FROZEN row (open
    dispute) is skipped. The transition + (future) balance credit happen in one commit;
    a re-run finds nothing still HELD (no double credit — TH-G/TH-J).
    """
    now = datetime.now(UTC)
    cutoff = now - RELEASE_AFTER
    released = 0
    async with session_factory() as session:
        holds = await repo.holds_ready_for_release(session, finalized_before=cutoff)
        for held in holds:
            # Re-check state under the same session (idempotent guard).
            if held.state != "HELD":
                continue
            held.state = "RELEASED"
            held.released_at = now
            # Balance credit (courier withdrawable) is Phase 11 — the ledger RELEASED row
            # is the source of truth the payout will read.
            released += 1
        await session.commit()
    logger.info("escrow.release_ready", released=released)
    return released


async def release_escrow(ctx: dict[str, Any]) -> int:
    """arq cron entrypoint (registered in WorkerSettings). Delegates to release_ready."""
    return await release_ready(ctx["session_factory"])
