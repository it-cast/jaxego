"""Repasse ao entregador na finalização da entrega.

Ao virar FINALIZADA, transfere `delivery.price_cents` da conta autenticada
(ITCAST — quem recebeu o PIX da loja) para a subconta Safe2Pay do entregador
(`courier.s2p_recipient_id`, criada na aprovação do KYC). Imediato — sem
retenção/escrow. Idempotente: uma vez setado `courier_payout_transaction_id`,
nunca repete. Degrada graciosamente em falha da Safe2Pay — a entrega já está
FINALIZADA independente do repasse; sem retry automático (TD a abrir).
"""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.couriers.models import Courier
from app.deliveries.models import Delivery
from app.payments.errors import PaymentGatewayError
from app.payments.port import PaymentPort

logger = structlog.get_logger("deliveries.payout")


async def payout_courier_on_finalize(
    session: AsyncSession, *, delivery: Delivery, payment: PaymentPort
) -> str | None:
    """Transfere o valor da entrega pro entregador. None se não aplicável/falhou."""
    if delivery.courier_payout_transaction_id:
        return delivery.courier_payout_transaction_id
    if delivery.courier_id is None or not delivery.price_cents:
        return None

    courier = await session.get(Courier, delivery.courier_id)
    if courier is None or not courier.s2p_recipient_id:
        logger.warning("delivery.payout_no_subaccount", delivery_id=delivery.id)
        return None

    try:
        result = await payment.payout(
            recipient=courier.s2p_recipient_id,
            amount_cents=delivery.price_cents,
            reference=f"dlv_{delivery.id}",
        )
    except PaymentGatewayError:
        logger.warning("delivery.payout_pending", delivery_id=delivery.id)
        return None

    delivery.courier_payout_transaction_id = result.transaction_id
    await session.flush()
    logger.info(
        "delivery.payout_completed",
        delivery_id=delivery.id,
        courier_id=courier.id,
        amount_cents=delivery.price_cents,
    )
    return result.transaction_id
