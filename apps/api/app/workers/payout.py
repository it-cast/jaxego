"""Repasse ao entregador — worker assíncrono (enfileirado, nunca bloqueante).

`payout_courier_task` é o entrypoint arq: roda `payout_courier_on_finalize` numa
sessão própria. `enqueue_payout` é chamado logo após a entrega virar FINALIZADA
(caminho imediato do entregador OU cron de 24h) — best-effort, espelha
`workers/dispatch.py::enqueue_dispatch`: uma falha ao enfileirar nunca derruba a
finalização (a entrega já está persistida; um re-enqueue manual recupera).
"""

from __future__ import annotations

from typing import Any

import structlog

from app.deliveries.models import Delivery
from app.deliveries.payout import payout_courier_on_finalize
from app.payments.factory import get_payment_adapter

logger = structlog.get_logger("workers.payout")


async def payout_courier_task(ctx: dict[str, Any], delivery_id: int) -> str:
    """arq entry point — repassa o valor da entrega finalizada pro entregador."""
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        delivery = await session.get(Delivery, delivery_id)
        if delivery is None or delivery.state != "FINALIZADA":
            return "skip-not-finalizada"
        result = await payout_courier_on_finalize(
            session, delivery=delivery, payment=get_payment_adapter()
        )
        await session.commit()
        return "paid" if result else "pending"


async def enqueue_payout(delivery_id: int) -> bool:
    """Enfileira o repasse pro entregador (best-effort; nunca bloqueia o caller)."""
    from arq import create_pool
    from arq.connections import RedisSettings

    from app.core.config import settings

    try:
        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        try:
            await pool.enqueue_job("payout_courier_task", delivery_id)
        finally:
            await pool.aclose()
        return True
    except Exception:  # noqa: BLE001 — never break finalize on a queue hiccup
        logger.warning("payout.enqueue_failed", delivery_id=delivery_id)
        return False
