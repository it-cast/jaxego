"""Courier Safe2Pay subaccount registration (Phase 10 — RN-010 / REQ-019).

Dois gatilhos:
- `register_subaccount_on_kyc_active`: acionado quando o KYC é aprovado (status → active).
  Usa CPF do entregador como Identity. Funciona para qualquer entregador.
- `register_subaccount_on_mei_active`: acionado quando MEI é validado (mei_pending=False).
  Atualiza a subconta existente ou cria nova usando CNPJ MEI.

Em ambos os casos degrada graciosamente se a API estiver indisponível — s2p_recipient_id
fica None e o entregador ainda opera no fluxo direto. CNPJ/CPF nunca logados (A09).
"""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.couriers.models import Courier
from app.payments.errors import PaymentGatewayError
from app.payments.port import PaymentPort

logger = structlog.get_logger("couriers.subaccount")


async def register_subaccount_on_kyc_active(
    session: AsyncSession,
    *,
    courier: Courier,
    payment: PaymentPort,
) -> str | None:
    """Cria subconta Safe2Pay ao ativar o KYC do entregador.

    Idempotente: se já tem s2p_recipient_id, retorna sem chamar a API.
    Degrada graciosamente em erro de gateway (retorna None).
    """
    if courier.s2p_recipient_id:
        return courier.s2p_recipient_id

    try:
        result = await payment.register_subaccount_full(courier=courier)
    except PaymentGatewayError:
        logger.warning("courier.subaccount_pending", courier_id=courier.id)
        return None

    courier.s2p_recipient_id = result["recipient_id"]
    courier.s2p_token = result["token"]
    await session.flush()
    logger.info("courier.subaccount_registered", courier_id=courier.id)
    return result["recipient_id"]


async def register_subaccount_on_mei_active(
    session: AsyncSession,
    *,
    courier: Courier,
    payment: PaymentPort,
    pix_key: str | None = None,
) -> str | None:
    """Atualiza/cria subconta Safe2Pay quando MEI é aprovado (RN-010).

    No-op quando MEI está pendente ou subconta já existe.
    """
    if courier.mei_pending or not courier.mei_cnpj:
        return None
    if courier.s2p_recipient_id:
        return courier.s2p_recipient_id

    try:
        result = await payment.register_subaccount_full(courier=courier)
    except PaymentGatewayError:
        logger.warning("courier.subaccount_pending", courier_id=courier.id)
        return None

    courier.s2p_recipient_id = result["recipient_id"]
    courier.s2p_token = result["token"]
    await session.flush()
    logger.info("courier.subaccount_registered", courier_id=courier.id)
    return result["recipient_id"]
