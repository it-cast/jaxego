"""Entregas da cidade para o admin da área: lista com filtros e detalhe com histórico.

Só leitura. Tudo filtrado pela área do token (TH-09: área no WHERE, entrega de outra
cidade → 404). O telefone do destinatário sai mascarado, como na lista da loja.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AreaScopeDep, CurrentUser, require_role
from app.core.exceptions import NotFoundError
from app.couriers.models import Courier
from app.db.session import get_session
from app.deliveries.models import Delivery, DeliveryStateTransition, Recipient
from app.deliveries.schemas import mask_phone_display
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood

router = APIRouter(prefix="/admin/deliveries", tags=["deliveries-admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AdminDep = Annotated[CurrentUser, Depends(require_role("admin_area"))]

LIMITE_MAX = 100


class AdminDeliveryItem(BaseModel):
    id: int
    state: str
    created_at: str | None
    scheduled_at: str | None
    merchant_id: int
    merchant_name: str | None
    courier_id: int | None
    courier_name: str | None
    pickup_address: str
    dropoff_address: str
    dropoff_number: str | None
    dropoff_neighborhood: str | None
    payment_method: str
    #: Como a corrida foi paga de fato: pix (inclui o PIX da plataforma), card ou direct.
    pagamento: str
    proof_method: str
    price_cents: int | None
    fee_cents: int
    reference_number: str | None
    public_token: str


class AdminDeliveryList(BaseModel):
    items: list[AdminDeliveryItem]
    total: int
    limit: int
    offset: int
    #: Quantas entregas há em cada status com os MESMOS filtros (menos o de status).
    por_estado: dict[str, int]


class AdminDeliveryTransition(BaseModel):
    from_state: str | None
    to_state: str
    actor_type: str | None
    reason: str | None
    created_at: str | None


class AdminDeliveryDetail(AdminDeliveryItem):
    dropoff_complement: str | None
    dropoff_reference: str | None
    recipient_name: str | None
    recipient_phone_masked: str | None
    items_description: str | None
    items_quantity: int
    notes: str | None
    distance_m: int | None
    accepted_at: str | None
    collected_at: str | None
    delivered_at: str | None
    finalized_at: str | None
    cancelled_at: str | None
    cancel_reason: str | None
    historico: list[AdminDeliveryTransition]


class FiltroOpcao(BaseModel):
    id: int
    nome: str


class AdminDeliveryFiltros(BaseModel):
    lojas: list[FiltroOpcao]
    entregadores: list[FiltroOpcao]


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _aware(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _base(area_id: int | None) -> Select:
    stmt = (
        select(Delivery, Merchant.trade_name, Courier.full_name, Neighborhood.name)
        .join(Merchant, Merchant.id == Delivery.merchant_id)
        .outerjoin(Courier, Courier.id == Delivery.courier_id)
        .outerjoin(Neighborhood, Neighborhood.id == Delivery.dropoff_neighborhood_id)
    )
    if area_id is not None:
        stmt = stmt.where(Delivery.area_id == area_id)
    return stmt


def _filtrar(
    stmt: Select,
    *,
    q: str | None,
    merchant_id: int | None,
    courier_id: int | None,
    payment_method: str | None,
    inicio: datetime | None,
    fim: datetime | None,
) -> Select:
    if q and q.strip():
        termo = q.strip().lstrip("#").strip()
        like = f"%{termo}%"
        conds = [
            Delivery.reference_number.ilike(like),
            Merchant.trade_name.ilike(like),
            Courier.full_name.ilike(like),
        ]
        if termo.isdigit():
            conds.insert(0, Delivery.id == int(termo))
        stmt = stmt.where(or_(*conds))
    if merchant_id is not None:
        stmt = stmt.where(Delivery.merchant_id == merchant_id)
    if courier_id is not None:
        stmt = stmt.where(Delivery.courier_id == courier_id)
    if payment_method == "pix":
        # O PIX da plataforma fica gravado como payment_method=direct + transação PIX.
        stmt = stmt.where(
            or_(Delivery.payment_method == "pix", Delivery.pix_transaction_id.is_not(None))
        )
    elif payment_method == "direct":
        stmt = stmt.where(
            Delivery.payment_method == "direct", Delivery.pix_transaction_id.is_(None)
        )
    elif payment_method:
        stmt = stmt.where(Delivery.payment_method == payment_method)
    if inicio is not None:
        stmt = stmt.where(Delivery.created_at >= _aware(inicio))
    if fim is not None:
        stmt = stmt.where(Delivery.created_at <= _aware(fim))
    return stmt


def _pagamento(d: Delivery) -> str:
    if d.payment_method == "pix" or d.pix_transaction_id:
        return "pix"
    return d.payment_method


def _item(d: Delivery, loja: str | None, entregador: str | None, bairro: str | None) -> dict:
    return {
        "id": d.id,
        "state": d.state,
        "created_at": _iso(d.created_at),
        "scheduled_at": _iso(d.scheduled_at),
        "merchant_id": d.merchant_id,
        "merchant_name": loja,
        "courier_id": d.courier_id,
        "courier_name": entregador,
        "pickup_address": d.pickup_address,
        "dropoff_address": d.dropoff_address,
        "dropoff_number": d.dropoff_number,
        "dropoff_neighborhood": bairro,
        "payment_method": d.payment_method,
        "pagamento": _pagamento(d),
        "proof_method": d.proof_method,
        "price_cents": d.price_cents,
        "fee_cents": d.fee_cents,
        "reference_number": d.reference_number,
        "public_token": d.public_token,
    }


@router.get("", response_model=AdminDeliveryList)
async def listar_entregas(
    _admin: AdminDep,
    scope: AreaScopeDep,
    session: SessionDep,
    q: str | None = Query(default=None, max_length=120),
    state: str | None = Query(
        default=None, max_length=200, description="Um ou mais, separados por vírgula"
    ),
    merchant_id: int | None = None,
    courier_id: int | None = None,
    payment_method: str | None = Query(default=None, max_length=20),
    inicio: datetime | None = None,
    fim: datetime | None = None,
    limit: int = 20,
    offset: int = 0,
) -> AdminDeliveryList:
    """Entregas da cidade, mais recentes primeiro. Busca por nº (#138), referência, loja
    ou entregador; filtros por status, loja, entregador, pagamento e período (criação)."""
    filtros = {
        "q": q,
        "merchant_id": merchant_id,
        "courier_id": courier_id,
        "payment_method": payment_method,
        "inicio": inicio,
        "fim": fim,
    }
    stmt = _filtrar(_base(scope), **filtros)

    # Contagem por status (com os demais filtros) — vira os atalhos da tela.
    por_estado_rows = await session.execute(
        stmt.with_only_columns(Delivery.state, func.count()).group_by(Delivery.state)
    )
    por_estado = dict(por_estado_rows.tuples().all())

    estados = [s.strip().upper() for s in (state or "").split(",") if s.strip()]
    if estados:
        stmt = stmt.where(Delivery.state.in_(estados))

    total = (
        await session.execute(stmt.with_only_columns(func.count(Delivery.id)).order_by(None))
    ).scalar_one()
    limit = max(1, min(limit, LIMITE_MAX))
    offset = max(offset, 0)
    rows = (
        await session.execute(stmt.order_by(Delivery.id.desc()).limit(limit).offset(offset))
    ).all()
    return AdminDeliveryList(
        items=[AdminDeliveryItem(**_item(*r)) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
        por_estado=por_estado,
    )


@router.get("/filtros", response_model=AdminDeliveryFiltros)
async def opcoes_de_filtro(
    _admin: AdminDep, scope: AreaScopeDep, session: SessionDep
) -> AdminDeliveryFiltros:
    """Lojas e entregadores da cidade, para os selects de filtro."""
    lojas_q = select(Merchant.id, Merchant.trade_name).order_by(Merchant.trade_name)
    entregadores_q = (
        select(Courier.id, Courier.full_name)
        .where(Courier.deleted_at.is_(None))
        .order_by(Courier.full_name)
    )
    if scope is not None:
        lojas_q = lojas_q.where(Merchant.area_id == scope)
        entregadores_q = entregadores_q.where(Courier.area_id == scope)
    lojas = [
        FiltroOpcao(id=i, nome=n or f"Loja {i}") for i, n in (await session.execute(lojas_q)).all()
    ]
    entregadores = [
        FiltroOpcao(id=i, nome=n or f"Entregador {i}")
        for i, n in (await session.execute(entregadores_q)).all()
    ]
    return AdminDeliveryFiltros(lojas=lojas, entregadores=entregadores)


@router.get("/{delivery_id}", response_model=AdminDeliveryDetail)
async def detalhe_entrega(
    delivery_id: int, _admin: AdminDep, scope: AreaScopeDep, session: SessionDep
) -> AdminDeliveryDetail:
    """Detalhe de uma entrega da cidade, com o histórico de status."""
    row = (await session.execute(_base(scope).where(Delivery.id == delivery_id))).first()
    if row is None:
        raise NotFoundError("Entrega não encontrada.")
    d = row[0]
    recipient = await session.get(Recipient, d.recipient_id) if d.recipient_id else None
    transicoes = (
        (
            await session.execute(
                select(DeliveryStateTransition)
                .where(DeliveryStateTransition.delivery_id == d.id)
                .order_by(DeliveryStateTransition.created_at, DeliveryStateTransition.id)
            )
        )
        .scalars()
        .all()
    )
    return AdminDeliveryDetail(
        **_item(*row),
        dropoff_complement=d.dropoff_complement,
        dropoff_reference=d.dropoff_reference,
        recipient_name=recipient.name if recipient else None,
        recipient_phone_masked=(
            mask_phone_display(recipient.phone_e164)
            if recipient and getattr(recipient, "phone_e164", None)
            else None
        ),
        items_description=d.items_description,
        items_quantity=d.items_quantity,
        notes=d.notes,
        distance_m=d.distance_m,
        accepted_at=_iso(d.accepted_at),
        collected_at=_iso(d.collected_at),
        delivered_at=_iso(d.delivered_at),
        finalized_at=_iso(d.finalized_at),
        cancelled_at=_iso(d.cancelled_at),
        cancel_reason=d.cancel_reason,
        historico=[
            AdminDeliveryTransition(
                from_state=t.from_state,
                to_state=t.to_state,
                actor_type=t.actor_type,
                reason=t.reason,
                created_at=_iso(t.created_at),
            )
            for t in transicoes
        ],
    )
