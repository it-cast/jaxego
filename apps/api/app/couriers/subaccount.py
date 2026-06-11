"""Courier Safe2Pay subaccount registration on MEI approval (Phase 10 — RN-010 / REQ-019).

When a courier's MEI becomes active (KYC approval, Phase 5 — `mei_pending=False`), we
register them as a Safe2Pay recipient/subaccount so the delivery split can pay their
corrida. Without an active MEI there is NO subaccount and therefore NO platform repasse
(the `direct` flow from Phase 7-9 still works). CNPJ/PIX-key are NEVER logged (A09).

`[ASSUMIDO A3]`: if the Safe2Pay subaccount API is unavailable / not supported, this
degrades gracefully — `s2p_recipient_id` stays None (a "pendência de cadastro manual"),
and the MEI hook remains valid for a later retry. The whole thing is behind `PaymentPort`,
so confirming the real API at T-13 changes only the adapter, not this hook.
"""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.couriers.models import Courier
from app.payments.errors import PaymentGatewayError
from app.payments.port import PaymentPort

logger = structlog.get_logger("couriers.subaccount")


async def register_subaccount_on_mei_active(
    session: AsyncSession,
    *,
    courier: Courier,
    payment: PaymentPort,
    pix_key: str | None = None,
) -> str | None:
    """Register the courier as a Safe2Pay subaccount iff the MEI is active (RN-010).

    No-op (returns None) when the MEI is pending or already has a recipient id. On a
    gateway error the registration degrades to a pending state (None) — it does NOT raise
    (A3 graceful degradation); the courier still works `direct`.
    """
    if courier.mei_pending or not courier.mei_cnpj:
        return None  # no active MEI → no subaccount (RN-010)
    if courier.s2p_recipient_id:
        return courier.s2p_recipient_id  # idempotent — already registered

    try:
        recipient_id = await payment.register_subaccount(
            courier_id=courier.id, mei_cnpj=courier.mei_cnpj, pix_key=pix_key
        )
    except PaymentGatewayError:
        # Degrade: leave s2p_recipient_id None (manual/retry pending). No CNPJ in the log.
        logger.warning("courier.subaccount_pending", courier_id=courier.id)
        return None

    courier.s2p_recipient_id = recipient_id
    await session.flush()
    logger.info("courier.subaccount_registered", courier_id=courier.id)
    return recipient_id
