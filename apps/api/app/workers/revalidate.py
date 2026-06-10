"""Receita revalidation job (E4) — retry windows 6/6/12/24h in aware UTC.

When signup hits E4 (Receita provider down), the merchant is created
`pending_validation` and this job revalidates on a backoff schedule. On a
successful "ativa" result it promotes the merchant to `active` (state machine +
audit, RN-012). Exhausting the windows escalates to the area admin (logged).
All datetimes are aware UTC (TD-010).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit
from app.integrations.base import ReceitaPort
from app.integrations.factory import get_receita_adapter
from app.merchants.models import Merchant
from app.merchants.state_machine import assert_transition

logger = structlog.get_logger("workers.revalidate")

# Backoff schedule (hours) between revalidation attempts (D-04 / REQ-008).
RETRY_WINDOWS_HOURS: tuple[int, ...] = (6, 6, 12, 24)


def next_retry_delay(attempt: int) -> timedelta | None:
    """Delay before the next attempt, or None once the schedule is exhausted."""
    if attempt >= len(RETRY_WINDOWS_HOURS):
        return None
    return timedelta(hours=RETRY_WINDOWS_HOURS[attempt])


async def revalidate_merchant(
    session: AsyncSession,
    *,
    merchant_id: int,
    receita: ReceitaPort,
    now: datetime | None = None,
) -> bool:
    """Revalidate one merchant against Receita; promote to active if ativa.

    Returns True if promoted. Updates `revalidation_attempts` and
    `next_revalidation_at` (aware UTC) for the next window; escalates on exhaust.
    """
    current = now or datetime.now(UTC)
    merchant = await session.get(Merchant, merchant_id)
    if merchant is None or merchant.status != "pending_validation":
        return False

    result = await receita.consultar_cnpj(merchant.document)
    if result is not None and result.situacao == "ativa":
        assert_transition(merchant.status, "active")
        merchant.status = "active"
        merchant.receita_validated = True
        merchant.next_revalidation_at = None
        await write_audit(
            session,
            actor_id=None,
            action="merchant.revalidated",
            area_id=merchant.area_id,
            before={"status": "pending_validation"},
            after={"status": "active", "merchant_id": merchant.id},
        )
        logger.info("merchant_revalidated", merchant_id=merchant.id)
        return True

    # Still down or inativa → schedule the next window (or escalate).
    merchant.revalidation_attempts += 1
    delay = next_retry_delay(merchant.revalidation_attempts)
    if delay is None:
        merchant.next_revalidation_at = None
        logger.warning("merchant_revalidation_exhausted", merchant_id=merchant.id)
        await write_audit(
            session,
            actor_id=None,
            action="merchant.revalidation_escalated",
            area_id=merchant.area_id,
            after={"merchant_id": merchant.id, "attempts": merchant.revalidation_attempts},
        )
    else:
        merchant.next_revalidation_at = current + delay
    return False


async def revalidate_receita(ctx: dict[str, Any], merchant_id: int) -> bool:
    """arq entrypoint: revalidate one merchant (adapter from the factory)."""
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        promoted = await revalidate_merchant(
            session, merchant_id=merchant_id, receita=get_receita_adapter()
        )
        await session.commit()
    return promoted
