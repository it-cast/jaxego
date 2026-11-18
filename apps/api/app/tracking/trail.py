"""Rastro do entregador (`courier_locations`): gravação, consulta e limpeza.

- O app manda a posição enquanto o entregador está online: a cada 5 min sem entrega,
  a cada 1 min com entrega ativa (ACEITA/COLETADA). A resposta do PATCH diz ao app
  qual intervalo usar (`interval_seconds`), então quem decide é o servidor.
- Pontos ruins não entram: precisão acima de 200 m, menos de 20 s depois do último,
  ou um salto impossível (> 200 km/h). A posição atual do entregador continua sendo
  atualizada como antes (despacho por proximidade).
- Quem vê: o admin da área (qualquer entregador da área, até 7 dias) e a loja (só o
  trajeto da entrega dela, entre o aceite e o fim). Cada consulta do admin vai para a
  auditoria.
- `purge_courier_locations` (cron diário) apaga o que passa de `rastro_retencao_dias`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import structlog
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.couriers.models import Courier
from app.db.mixins import ensure_aware_utc
from app.deliveries.models import Delivery
from app.tracking.models import CourierLocation, DeliveryLocation

logger = structlog.get_logger(__name__)

INTERVALO_COM_ENTREGA_S = 60
INTERVALO_SEM_ENTREGA_S = 300
PRECISAO_MAX_M = 200.0
INTERVALO_MIN_S = 20
VELOCIDADE_MAX_KMH = 200.0
ESTADOS_ATIVOS = ("ACEITA", "COLETADA")
MAX_PONTOS = 5000
LOTE_LIMPEZA = 5000


# ---------------------------------------------------------------------------
# Contratos
# ---------------------------------------------------------------------------
class TrailPoint(BaseModel):
    lat: float
    lng: float
    at: str
    accuracy_m: float | None = None
    delivery_id: int | None = None


class TrailAction(BaseModel):
    action: str
    lat: float
    lng: float
    at: str
    delivery_id: int


class TrailOut(BaseModel):
    courier_id: int
    courier_name: str | None = None
    start: str
    end: str
    delivery_id: int | None = None
    points: list[TrailPoint]
    actions: list[TrailAction]
    distance_km: float
    retention_days: int
    truncated: bool = False


class TrailPeriodError(AppError):
    status_code = 422
    code = "trail_period_invalid"


# ---------------------------------------------------------------------------
# Cálculo
# ---------------------------------------------------------------------------
def distancia_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def distancia_total_km(pontos: list[tuple[float, float]]) -> float:
    total = sum(distancia_m(*pontos[i - 1], *pontos[i]) for i in range(1, len(pontos)))
    return round(total / 1000, 2)


def _iso(dt: datetime) -> str:
    return ensure_aware_utc(dt).isoformat()


# ---------------------------------------------------------------------------
# Gravação (PATCH /couriers/{id}/location)
# ---------------------------------------------------------------------------
@dataclass
class ResultadoPonto:
    interval_seconds: int
    recorded: bool


async def entrega_ativa(session: AsyncSession, courier_id: int) -> int | None:
    """Entrega ativa mais recente do entregador (pode haver mais de uma simultânea)."""
    return (
        await session.execute(
            select(Delivery.id)
            .where(Delivery.courier_id == courier_id, Delivery.state.in_(ESTADOS_ATIVOS))
            .order_by(Delivery.accepted_at.desc(), Delivery.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def registrar_ponto(
    session: AsyncSession,
    *,
    courier: Courier,
    lat: float,
    lng: float,
    accuracy_m: float | None,
    agora: datetime | None = None,
) -> ResultadoPonto:
    """Grava o ponto do rastro (se for bom) e diz ao app o próximo intervalo. Só online."""
    # Coluna sem fração de segundo: grava já truncado (o MySQL arredondaria)
    agora = (agora or datetime.now(UTC)).replace(microsecond=0)
    ativa = await entrega_ativa(session, courier.id)
    intervalo = INTERVALO_COM_ENTREGA_S if ativa else INTERVALO_SEM_ENTREGA_S
    teste = get_settings().rastro_intervalo_teste_s
    if teste and ativa:  # teste local: só com entrega ativa; sem entrega segue 5 min
        intervalo = teste
    espaco_min = min(INTERVALO_MIN_S, max(1, intervalo - 3))
    if not courier.is_online:
        return ResultadoPonto(intervalo, False)
    if accuracy_m is not None and accuracy_m > PRECISAO_MAX_M:
        return ResultadoPonto(intervalo, False)
    ultimo = (
        await session.execute(
            select(CourierLocation)
            .where(CourierLocation.courier_id == courier.id)
            .order_by(CourierLocation.recorded_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if ultimo is not None:
        segundos = (agora - ensure_aware_utc(ultimo.recorded_at)).total_seconds()
        if segundos < espaco_min:
            return ResultadoPonto(intervalo, False)
        kmh = distancia_m(ultimo.lat, ultimo.lng, lat, lng) / 1000 / (segundos / 3600)
        if kmh > VELOCIDADE_MAX_KMH:
            logger.info("trail_point_jump_ignored", courier_id=courier.id)
            return ResultadoPonto(intervalo, False)
    session.add(
        CourierLocation(
            area_id=courier.area_id,
            courier_id=courier.id,
            delivery_id=ativa,
            lat=lat,
            lng=lng,
            accuracy_m=accuracy_m,
            recorded_at=agora,
        )
    )
    await session.flush()
    return ResultadoPonto(intervalo, True)


# ---------------------------------------------------------------------------
# Consulta
# ---------------------------------------------------------------------------
async def _montar(
    session: AsyncSession,
    *,
    courier: Courier,
    inicio: datetime,
    fim: datetime,
    delivery_id: int | None,
) -> TrailOut:
    linhas = (
        (
            await session.execute(
                select(CourierLocation)
                .where(
                    CourierLocation.courier_id == courier.id,
                    CourierLocation.recorded_at >= inicio,
                    CourierLocation.recorded_at <= fim,
                )
                .order_by(CourierLocation.recorded_at)
                .limit(MAX_PONTOS + 1)
            )
        )
        .scalars()
        .all()
    )
    truncado = len(linhas) > MAX_PONTOS
    linhas = linhas[:MAX_PONTOS]
    filtro_acoes = [
        DeliveryLocation.courier_id == courier.id,
        DeliveryLocation.recorded_at >= inicio,
        DeliveryLocation.recorded_at <= fim,
    ]
    if delivery_id is not None:
        filtro_acoes.append(DeliveryLocation.delivery_id == delivery_id)
    acoes = (
        (
            await session.execute(
                select(DeliveryLocation).where(*filtro_acoes).order_by(DeliveryLocation.recorded_at)
            )
        )
        .scalars()
        .all()
    )
    # A linha do trajeto junta os pontos periódicos e as ações (que também têm GPS), em ordem
    juntos = sorted(
        [(ensure_aware_utc(p.recorded_at), p.lat, p.lng) for p in linhas]
        + [(ensure_aware_utc(a.recorded_at), a.lat, a.lng) for a in acoes]
    )
    return TrailOut(
        courier_id=courier.id,
        courier_name=courier.full_name,
        start=_iso(inicio),
        end=_iso(fim),
        delivery_id=delivery_id,
        points=[
            TrailPoint(
                lat=p.lat,
                lng=p.lng,
                at=_iso(p.recorded_at),
                accuracy_m=p.accuracy_m,
                delivery_id=p.delivery_id,
            )
            for p in linhas
        ],
        actions=[
            TrailAction(
                action=a.action,
                lat=a.lat,
                lng=a.lng,
                at=_iso(a.recorded_at),
                delivery_id=a.delivery_id,
            )
            for a in acoes
        ],
        distance_km=distancia_total_km([(lat, lng) for _, lat, lng in juntos]),
        retention_days=get_settings().rastro_retencao_dias,
        truncated=truncado,
    )


async def rastro_do_entregador(
    session: AsyncSession,
    *,
    courier: Courier,
    inicio: datetime,
    fim: datetime,
    agora: datetime | None = None,
) -> TrailOut:
    """Admin da área: o rastro de um período (máx. 24 h, dentro da retenção)."""
    agora = agora or datetime.now(UTC)
    inicio, fim = ensure_aware_utc(inicio), ensure_aware_utc(fim)
    if fim <= inicio:
        raise TrailPeriodError("O fim do período precisa ser depois do início.")
    if fim - inicio > timedelta(hours=24):
        raise TrailPeriodError("Consulte no máximo 24 horas por vez.")
    dias = get_settings().rastro_retencao_dias
    limite = agora - timedelta(days=dias)
    if fim < limite:
        raise TrailPeriodError(
            f"O rastro fica guardado por {dias} dias; esse período já foi apagado."
        )
    return await _montar(
        session, courier=courier, inicio=max(inicio, limite), fim=min(fim, agora), delivery_id=None
    )


def janela_da_entrega(d: Delivery, agora: datetime) -> tuple[datetime, datetime] | None:
    """Do aceite até o fim da entrega (entregue/cancelada/finalizada); ativa = até agora."""
    if d.accepted_at is None:
        return None
    inicio = ensure_aware_utc(d.accepted_at)
    fins = [
        ensure_aware_utc(x)
        for x in (d.delivered_at, d.cancelled_at, d.finalized_at)
        if x is not None
    ]
    fim = min(fins) if fins else agora
    if d.state in ESTADOS_ATIVOS:
        fim = agora
    return inicio, max(fim, inicio)


async def rastro_da_entrega(
    session: AsyncSession, *, delivery: Delivery, agora: datetime | None = None
) -> TrailOut | None:
    """Loja (e admin): o trajeto do entregador durante a entrega. Sem entregador/aceite: None."""
    agora = agora or datetime.now(UTC)
    if delivery.courier_id is None:
        return None
    janela = janela_da_entrega(delivery, agora)
    if janela is None:
        return None
    courier = await session.get(Courier, delivery.courier_id)
    if courier is None:
        return None
    return await _montar(
        session, courier=courier, inicio=janela[0], fim=janela[1], delivery_id=delivery.id
    )


class TrailDelivery(BaseModel):
    """Entrega do entregador dentro da retenção (para escolher no filtro do rastro)."""

    id: int
    state: str
    merchant_name: str | None
    accepted_at: str
    ended_at: str | None


async def entregas_recentes(
    session: AsyncSession,
    *,
    courier: Courier,
    inicio: datetime | None = None,
    fim: datetime | None = None,
    agora: datetime | None = None,
    limite: int = 100,
) -> list[TrailDelivery]:
    """Entregas do entregador que têm pontos no rastro (`courier_locations`) dentro da
    retenção, da que tem o ponto mais recente para a mais antiga. Com `inicio`/`fim`,
    só as que têm ponto nesse período."""
    from app.merchants.models import Merchant

    agora = agora or datetime.now(UTC)
    desde = agora - timedelta(days=get_settings().rastro_retencao_dias)
    if inicio is not None:
        desde = max(desde, ensure_aware_utc(inicio))
    filtros = [
        CourierLocation.courier_id == courier.id,
        CourierLocation.delivery_id.is_not(None),
        CourierLocation.recorded_at >= desde,
    ]
    if fim is not None:
        filtros.append(CourierLocation.recorded_at <= ensure_aware_utc(fim))
    ultimos = (
        select(
            CourierLocation.delivery_id.label("delivery_id"),
            func.max(CourierLocation.recorded_at).label("ultimo"),
        )
        .where(*filtros)
        .group_by(CourierLocation.delivery_id)
        .subquery()
    )
    rows = (
        await session.execute(
            select(Delivery, Merchant.trade_name)
            .join(ultimos, ultimos.c.delivery_id == Delivery.id)
            .outerjoin(Merchant, Merchant.id == Delivery.merchant_id)
            .where(Delivery.courier_id == courier.id, Delivery.area_id == courier.area_id)
            .order_by(ultimos.c.ultimo.desc(), Delivery.id.desc())
            .limit(limite)
        )
    ).all()
    out: list[TrailDelivery] = []
    for d, loja in rows:
        janela = janela_da_entrega(d, agora)
        if janela is None:
            continue
        ativa = d.state in ESTADOS_ATIVOS
        out.append(
            TrailDelivery(
                id=d.id,
                state=str(getattr(d.state, "value", d.state)),
                merchant_name=loja,
                accepted_at=_iso(janela[0]),
                ended_at=None if ativa else _iso(janela[1]),
            )
        )
    return out


@dataclass
class Posicao:
    lat: float
    lng: float
    at: datetime


async def ultima_posicao_na_entrega(session: AsyncSession, *, delivery: Delivery) -> Posicao | None:
    """Posição mais recente do entregador durante a entrega: a última ação (com GPS) ou o
    último ponto do rastro desde o aceite, o que for mais novo. É o que o rastreio mostra."""
    acao = (
        (
            await session.execute(
                select(DeliveryLocation)
                .where(DeliveryLocation.delivery_id == delivery.id)
                .order_by(DeliveryLocation.recorded_at.desc())
                .limit(1)
            )
        )
        .scalars()
        .first()
    )
    melhor = Posicao(acao.lat, acao.lng, ensure_aware_utc(acao.recorded_at)) if acao else None
    if delivery.courier_id is not None and delivery.accepted_at is not None:
        ponto = (
            (
                await session.execute(
                    select(CourierLocation)
                    .where(
                        CourierLocation.courier_id == delivery.courier_id,
                        CourierLocation.recorded_at >= delivery.accepted_at,
                    )
                    .order_by(CourierLocation.recorded_at.desc())
                    .limit(1)
                )
            )
            .scalars()
            .first()
        )
        if ponto is not None and (
            melhor is None or ensure_aware_utc(ponto.recorded_at) > melhor.at
        ):
            melhor = Posicao(ponto.lat, ponto.lng, ensure_aware_utc(ponto.recorded_at))
    return melhor


# ---------------------------------------------------------------------------
# Limpeza (cron diário)
# ---------------------------------------------------------------------------
async def purge_courier_locations(ctx: dict) -> int:
    """Apaga pontos mais velhos que `rastro_retencao_dias`, em lotes. Devolve quantos apagou."""
    session_factory: async_sessionmaker[AsyncSession] = ctx["session_factory"]
    corte = datetime.now(UTC) - timedelta(days=get_settings().rastro_retencao_dias)
    total = 0
    while True:
        async with session_factory() as s:
            ids = (
                (
                    await s.execute(
                        select(CourierLocation.id)
                        .where(CourierLocation.recorded_at < corte)
                        .limit(LOTE_LIMPEZA)
                    )
                )
                .scalars()
                .all()
            )
            if not ids:
                break
            await s.execute(delete(CourierLocation).where(CourierLocation.id.in_(ids)))
            await s.commit()
            total += len(ids)
        if len(ids) < LOTE_LIMPEZA:
            break
    logger.info("courier_locations_purged", deleted=total)
    return total
