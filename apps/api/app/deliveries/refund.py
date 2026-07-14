"""Estorno do PIX ao cancelar uma entrega paga via `platform_pix`.

Ao virar CANCELADA, estorna o valor cobrado no PIX (`platform_charges.amount_cents`
— já é só a parte que o Safe2Pay realmente recebeu, descontado o saldo usado, ver
`deliveries/service.py::create_delivery`) via `DELETE /v2/pix/cancel/{idTransaction}`
(contrato confirmado — token da conta autenticada, ITCAST filha). Não é síncrono do
lado da Safe2Pay: o status final (`platform_charges.status = "refunded"`) chega pelo
webhook (event_status "6", já tratado em `payments/webhooks_router.py`) — esta função
só DISPARA o estorno, nunca marca o status ela mesma (evitaria a condição de corrida
com o webhook, que só transiciona `paid` → `refunded`).

Degrada graciosamente em falha da Safe2Pay — a entrega já está CANCELADA
independente do estorno; sem retry automático (mesmo padrão de `payout.py`, TD a
abrir). A devolução do saldo usado (`credit_applied_cents`) é local e SÍNCRONA
(ver `cancel_delivery`) — não depende deste estorno externo.
"""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.deliveries.models import Delivery
from app.payments import repo as payments_repo
from app.payments.errors import PaymentGatewayError
from app.payments.port import PaymentPort

logger = structlog.get_logger("deliveries.refund")


async def refund_delivery_on_cancel(
    session: AsyncSession, *, delivery: Delivery, payment: PaymentPort
) -> bool:
    """Estorna o PIX da entrega cancelada. True se o estorno foi disparado."""
    charge = await payments_repo.get_charge_by_delivery(session, delivery_id=delivery.id)
    if charge is None or charge.status != "paid" or not charge.transaction_id:
        return False
    if charge.method != "pix":
        logger.warning("delivery.refund_unsupported_method", delivery_id=delivery.id, method=charge.method)
        return False

    try:
        await payment.refund(
            transaction_id=charge.transaction_id,
            amount_cents=charge.amount_cents,
            method="pix",
        )
    except PaymentGatewayError:
        logger.warning("delivery.refund_pending", delivery_id=delivery.id)
        return False

    logger.info(
        "delivery.refund_requested",
        delivery_id=delivery.id,
        transaction_id=charge.transaction_id,
        amount_cents=charge.amount_cents,
    )
    return True
