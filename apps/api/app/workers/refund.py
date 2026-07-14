"""Estorno do PIX ao cancelar uma entrega — worker assíncrono (enfileirado, nunca bloqueante).

`refund_delivery_task` é o entrypoint arq: roda `refund_delivery_on_cancel` numa sessão
própria. `enqueue_refund` é chamado logo após a entrega virar CANCELADA — best-effort,
espelha `workers/payout.py::enqueue_payout`: uma falha ao enfileirar nunca derruba o
cancelamento (a entrega já está persistida; um re-enqueue manual recupera).
"""

from __future__ import annotations

from typing import Any

import structlog

from app.deliveries.models import Delivery
from app.deliveries.refund import refund_delivery_on_cancel
from app.payments.factory import get_payment_adapter

logger = structlog.get_logger("workers.refund")


async def refund_delivery_task(ctx: dict[str, Any], delivery_id: int) -> str:
    """arq entry point — estorna o PIX da entrega cancelada."""
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        delivery = await session.get(Delivery, delivery_id)
        if delivery is None or delivery.state != "CANCELADA":
            return "skip-not-cancelada"
        requested = await refund_delivery_on_cancel(
            session, delivery=delivery, payment=get_payment_adapter()
        )
        await session.commit()
        return "requested" if requested else "skip-no-charge"


async def enqueue_refund(delivery_id: int) -> bool:
    """Enfileira o estorno do PIX (best-effort; nunca bloqueia o caller)."""
    from arq import create_pool
    from arq.connections import RedisSettings

    from app.core.config import settings

    try:
        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        try:
            await pool.enqueue_job("refund_delivery_task", delivery_id)
        finally:
            await pool.aclose()
        return True
    except Exception:  # noqa: BLE001 — never break cancel on a queue hiccup
        logger.warning("refund.enqueue_failed", delivery_id=delivery_id)
        return False
