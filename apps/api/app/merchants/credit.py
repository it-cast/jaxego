"""Saldo/crédito da loja (opt-in) — apuração na finalização, uso na criação.

Duas pontas, nunca automáticas em relação ao consumo:

1. **Apuração** (`reconcile_delivery_credit`): na FINALIZAÇÃO de uma entrega
   `platform_pix`, compara `Delivery.pix_courier_price_cents` (o preço do
   entregador mais caro elegível, cobrado no PIX) com `Delivery.price_cents`
   (o que o entregador que realmente aceitou cobra). Sobrou dinheiro → crédito
   pra loja. Faltou → débito. Idempotente (uma apuração por entrega).

2. **Consumo** (`apply_credit`): na CRIAÇÃO de uma entrega nova, a loja ESCOLHE
   quanto do saldo disponível quer usar como desconto (nunca aplicado sozinho).
   O valor pedido é sempre reclampado no servidor contra o saldo real e contra
   o total da cobrança — nunca confia no número que o cliente mandou.

Saldo é DERIVADO (soma do ledger sob `FOR UPDATE`), nunca um campo solto —
mesmo padrão de `app/withdrawals/repo.py::available_balance_cents`, pra evitar
corrida entre duas entregas mexendo no saldo da mesma loja ao mesmo tempo.
Saldo pode ficar NEGATIVO (falta apurada) — não bloqueia novas entregas; a
próxima sobra compensa sozinha (soma do ledger).
"""

from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deliveries.models import Delivery
from app.merchants.models import MerchantCreditLedger

logger = structlog.get_logger("merchants.credit")


async def _locked_entries(
    session: AsyncSession, *, area_id: int, merchant_id: int
) -> list[MerchantCreditLedger]:
    stmt = (
        select(MerchantCreditLedger)
        .where(
            MerchantCreditLedger.area_id == area_id,
            MerchantCreditLedger.merchant_id == merchant_id,
        )
        .with_for_update()
    )
    return list((await session.execute(stmt)).scalars().all())


async def available_credit_cents(
    session: AsyncSession, *, area_id: int, merchant_id: int
) -> int:
    """Saldo atual da loja (pode ser negativo). Trava as linhas — chamar dentro
    da mesma transação que vai gravar o consumo, pra serializar concorrência."""
    entries = await _locked_entries(session, area_id=area_id, merchant_id=merchant_id)
    return sum(e.amount_cents for e in entries)


async def list_ledger(
    session: AsyncSession, *, area_id: int, merchant_id: int, limit: int = 50, offset: int = 0
) -> list[MerchantCreditLedger]:
    """Extrato (somente leitura, sem lock) — mais recentes primeiro."""
    stmt = (
        select(MerchantCreditLedger)
        .where(
            MerchantCreditLedger.area_id == area_id,
            MerchantCreditLedger.merchant_id == merchant_id,
        )
        .order_by(MerchantCreditLedger.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list((await session.execute(stmt)).scalars().all())


async def preview_credit_cents(
    session: AsyncSession, *, area_id: int, merchant_id: int, requested_cents: int, charge_cents: int
) -> int:
    """Reclampa o quanto a LOJA pediu pra usar de saldo, ANTES de a entrega existir.

    `[0, saldo_disponível, charge_cents]` — nunca confia no valor do cliente.
    Trava as linhas do ledger (mesma trava de `available_credit_cents`); a trava
    fica de pé até o fim da transação, então `record_consumption` (chamado
    depois, já com o `delivery_id`) pode reusar este mesmo valor com segurança
    — ninguém mais consegue mexer no saldo da loja no meio do caminho.
    """
    if requested_cents <= 0 or charge_cents <= 0:
        return 0
    available = await available_credit_cents(session, area_id=area_id, merchant_id=merchant_id)
    return max(0, min(requested_cents, available, charge_cents))


async def record_consumption(
    session: AsyncSession, *, area_id: int, merchant_id: int, delivery_id: int, amount_cents: int
) -> None:
    """Grava o lançamento de consumo (negativo) — `amount_cents` já deve vir
    clampado por `preview_credit_cents` na mesma transação. No-op se <= 0."""
    if amount_cents <= 0:
        return
    session.add(
        MerchantCreditLedger(
            area_id=area_id,
            merchant_id=merchant_id,
            delivery_id=delivery_id,
            kind="consumption",
            amount_cents=-amount_cents,
            reason="Saldo usado como desconto na criação da entrega",
        )
    )
    await session.flush()
    logger.info(
        "merchant_credit.applied",
        merchant_id=merchant_id,
        delivery_id=delivery_id,
        applied_cents=amount_cents,
    )


async def record_topup(
    session: AsyncSession, *, area_id: int, merchant_id: int, charge_id: int, amount_cents: int
) -> None:
    """Grava a recarga de saldo (positivo) quando o PIX é confirmado pelo webhook.

    `amount_cents` é só a parte que vira saldo (net_amount_cents da cobrança — sem
    taxa_pix/taxa_servico). Idempotente por `charge_id` (uma cobrança credita o saldo
    no máximo uma vez, mesmo se o webhook reenviar — TH-E já filtra a maioria dos
    reenvios, isso é a segunda camada). No-op se <= 0."""
    if amount_cents <= 0:
        return
    existing = (
        await session.execute(
            select(MerchantCreditLedger.id).where(
                MerchantCreditLedger.charge_id == charge_id,
                MerchantCreditLedger.kind == "topup",
            )
        )
    ).first()
    if existing is not None:
        return
    session.add(
        MerchantCreditLedger(
            area_id=area_id,
            merchant_id=merchant_id,
            delivery_id=None,
            charge_id=charge_id,
            kind="topup",
            amount_cents=amount_cents,
            reason="Recarga de saldo via PIX",
        )
    )
    await session.flush()
    logger.info(
        "merchant_credit.topup",
        merchant_id=merchant_id,
        charge_id=charge_id,
        amount_cents=amount_cents,
    )


async def reverse_consumption(
    session: AsyncSession, *, area_id: int, merchant_id: int, delivery_id: int, amount_cents: int
) -> None:
    """Devolve o saldo usado quando a entrega é CANCELADA (o PIX correspondente
    também é estornado integralmente — ver `deliveries/service.py::cancel_delivery`).
    Idempotente: se já existe um `reversal` pra esta entrega, não repete. No-op
    se <= 0 (entrega não usou saldo)."""
    if amount_cents <= 0:
        return
    existing = (
        await session.execute(
            select(MerchantCreditLedger.id).where(
                MerchantCreditLedger.delivery_id == delivery_id,
                MerchantCreditLedger.kind == "reversal",
            )
        )
    ).first()
    if existing is not None:
        return
    session.add(
        MerchantCreditLedger(
            area_id=area_id,
            merchant_id=merchant_id,
            delivery_id=delivery_id,
            kind="reversal",
            amount_cents=amount_cents,
            reason="Saldo devolvido — entrega cancelada",
        )
    )
    await session.flush()
    logger.info(
        "merchant_credit.reversed",
        merchant_id=merchant_id,
        delivery_id=delivery_id,
        reversed_cents=amount_cents,
    )


async def reconcile_delivery_credit(session: AsyncSession, *, delivery: Delivery) -> None:
    """Apura sobra/falta na FINALIZAÇÃO de uma entrega `platform_pix`.

    Idempotente: se já existe um lançamento `reconciliation` para esta
    entrega, não repete (chamada pode acontecer no caminho imediato de
    finalização OU no cron de 24h de segurança — nunca os dois pra mesma
    entrega, mas o guard fica por segurança).
    """
    if delivery.pix_courier_price_cents is None or delivery.price_cents is None:
        return  # entrega não usou platform_pix, ou preço do entregador não resolvido

    existing = (
        await session.execute(
            select(MerchantCreditLedger.id).where(
                MerchantCreditLedger.delivery_id == delivery.id,
                MerchantCreditLedger.kind == "reconciliation",
            )
        )
    ).first()
    if existing is not None:
        return

    diff = delivery.pix_courier_price_cents - delivery.price_cents
    if diff == 0:
        return  # entregador cobrou exatamente o que foi pago — nada a apurar

    reason = (
        f"Entregador cobrou R$ {delivery.price_cents / 100:.2f}, "
        f"PIX pagou R$ {delivery.pix_courier_price_cents / 100:.2f}"
    )
    session.add(
        MerchantCreditLedger(
            area_id=delivery.area_id,
            merchant_id=delivery.merchant_id,
            delivery_id=delivery.id,
            kind="reconciliation",
            amount_cents=diff,
            reason=reason,
        )
    )
    await session.flush()
    logger.info(
        "merchant_credit.reconciled",
        merchant_id=delivery.merchant_id,
        delivery_id=delivery.id,
        diff_cents=diff,
    )
