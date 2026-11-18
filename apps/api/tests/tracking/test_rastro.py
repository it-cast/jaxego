"""Rastro do entregador (courier_locations): gravação, consulta e limpeza.

SQLite em memória (conftest). Dados sintéticos.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.areas.models import Area
from app.couriers.models import Courier
from app.deliveries.models import Delivery
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from app.tracking import trail
from app.tracking.models import CourierLocation, DeliveryLocation
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.helpers import make_team

pytestmark = pytest.mark.asyncio

T0 = datetime(2026, 11, 18, 12, 0, tzinfo=UTC)


async def _base(s: AsyncSession, *, online: bool = True) -> tuple[Area, Courier, Merchant, Neighborhood]:
    area = Area(codename="padua", name="Pádua", config={})
    s.add(area)
    await s.flush()
    courier = Courier(
        area_id=area.id,
        team_id=(await make_team(s, area_id=area.id)).id,
        password_hash="x",
        cpf="11122233344",
        full_name="Pedro Entregador",
        phone_e164="+5522988887777",
        email="pedro@example.com",
        status="active",
        is_online=online,
    )
    merchant = Merchant(
        area_id=area.id,
        account_type="cnpj",
        document="11222333000181",
        trade_name="Loja",
        category="restaurante",
        phone_e164="+5522999991111",
        email="loja@example.com",
        status="active",
    )
    nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
    s.add_all([courier, merchant, nbhd])
    await s.flush()
    return area, courier, merchant, nbhd


async def _entrega(s, area, courier, merchant, nbhd, *, state="ACEITA", accepted_at=T0, delivered_at=None, token="T"):
    d = Delivery(
        area_id=area.id,
        merchant_id=merchant.id,
        courier_id=courier.id,
        state=state,
        dispatch_mode="direct",
        payment_method="card",
        proof_method="photo",
        pickup_address="a",
        dropoff_address="b",
        dropoff_neighborhood_id=nbhd.id,
        fee_cents=0,
        items_quantity=1,
        public_token=(token * 26)[:26],
        origin="manual",
        accepted_at=accepted_at,
        delivered_at=delivered_at,
    )
    s.add(d)
    await s.flush()
    return d


async def _pontos(s: AsyncSession) -> list[CourierLocation]:
    return list((await s.execute(select(CourierLocation).order_by(CourierLocation.recorded_at))).scalars().all())


async def test_grava_so_online_com_filtros_e_intervalo_pelo_servidor(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area, courier, merchant, nbhd = await _base(s)
        r = await trail.registrar_ponto(s, courier=courier, lat=-21.54, lng=-42.18, accuracy_m=10, agora=T0)
        assert (r.interval_seconds, r.recorded) == (300, True)
        # menos de 20 s depois: não grava
        r = await trail.registrar_ponto(s, courier=courier, lat=-21.541, lng=-42.18, accuracy_m=10, agora=T0 + timedelta(seconds=10))
        assert r.recorded is False
        # precisão ruim: não grava
        r = await trail.registrar_ponto(s, courier=courier, lat=-21.541, lng=-42.18, accuracy_m=500, agora=T0 + timedelta(minutes=5))
        assert r.recorded is False
        # salto impossível (~110 km em 1 min): não grava
        r = await trail.registrar_ponto(s, courier=courier, lat=-20.54, lng=-42.18, accuracy_m=10, agora=T0 + timedelta(minutes=6))
        assert r.recorded is False
        # com entrega ativa: intervalo de 1 min e o ponto leva a entrega
        d = await _entrega(s, area, courier, merchant, nbhd)
        r = await trail.registrar_ponto(s, courier=courier, lat=-21.545, lng=-42.18, accuracy_m=None, agora=T0 + timedelta(minutes=7))
        assert (r.interval_seconds, r.recorded) == (60, True)
        pts = await _pontos(s)
        assert [p.delivery_id for p in pts] == [None, d.id]
        # offline: não grava
        courier.is_online = False
        r = await trail.registrar_ponto(s, courier=courier, lat=-21.55, lng=-42.18, accuracy_m=5, agora=T0 + timedelta(minutes=9))
        assert r.recorded is False
        assert len(await _pontos(s)) == 2


async def test_rastro_do_periodo_junta_pontos_e_acoes_e_valida_o_periodo(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area, courier, merchant, nbhd = await _base(s)
        d = await _entrega(s, area, courier, merchant, nbhd)
        for i, lat in enumerate([-21.540, -21.545, -21.550]):
            s.add(CourierLocation(area_id=area.id, courier_id=courier.id, lat=lat, lng=-42.18, recorded_at=T0 + timedelta(minutes=i)))
        s.add(DeliveryLocation(area_id=area.id, delivery_id=d.id, courier_id=courier.id, action="coletou", lat=-21.5425, lng=-42.18, recorded_at=T0 + timedelta(seconds=30)))
        await s.flush()
        agora = T0 + timedelta(hours=1)
        out = await trail.rastro_do_entregador(s, courier=courier, inicio=T0 - timedelta(hours=1), fim=agora, agora=agora)
        assert [p.lat for p in out.points] == [-21.540, -21.545, -21.550]
        assert [a.action for a in out.actions] == ["coletou"]
        assert out.distance_km == pytest.approx(1.11, abs=0.02)  # ~1,1 km em linha
        assert out.courier_name == "Pedro Entregador"
        assert out.retention_days == 7

        with pytest.raises(trail.TrailPeriodError):
            await trail.rastro_do_entregador(s, courier=courier, inicio=agora, fim=T0, agora=agora)
        with pytest.raises(trail.TrailPeriodError):
            await trail.rastro_do_entregador(s, courier=courier, inicio=T0 - timedelta(hours=30), fim=T0, agora=agora)
        with pytest.raises(trail.TrailPeriodError):
            await trail.rastro_do_entregador(s, courier=courier, inicio=T0 - timedelta(days=10), fim=T0 - timedelta(days=9, hours=12), agora=agora)


async def test_rastro_da_entrega_vai_do_aceite_ao_fim(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area, courier, merchant, nbhd = await _base(s)
        d = await _entrega(s, area, courier, merchant, nbhd, state="ENTREGUE", accepted_at=T0, delivered_at=T0 + timedelta(minutes=20))
        for m in (-5, 1, 10, 19, 30):  # antes do aceite e depois da entrega ficam de fora
            s.add(CourierLocation(area_id=area.id, courier_id=courier.id, lat=-21.54 - m / 10000, lng=-42.18, recorded_at=T0 + timedelta(minutes=m)))
        await s.flush()
        out = await trail.rastro_da_entrega(s, delivery=d, agora=T0 + timedelta(hours=2))
        assert out is not None and out.delivery_id == d.id
        assert len(out.points) == 3

        sem_aceite = await _entrega(s, area, courier, merchant, nbhd, state="CRIADA", accepted_at=None, token="U")
        assert await trail.rastro_da_entrega(s, delivery=sem_aceite) is None


async def test_limpeza_apaga_so_o_que_passou_da_retencao(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    agora = datetime.now(UTC)
    async with session_factory() as s:
        area, courier, _, _ = await _base(s)
        for dias in (10, 8, 6, 1):
            s.add(CourierLocation(area_id=area.id, courier_id=courier.id, lat=-21.54, lng=-42.18, recorded_at=agora - timedelta(days=dias)))
        await s.commit()
    assert await trail.purge_courier_locations({"session_factory": session_factory}) == 2
    async with session_factory() as s:
        assert (await s.execute(select(func.count()).select_from(CourierLocation))).scalar_one() == 2
    assert await trail.purge_courier_locations({"session_factory": session_factory}) == 0


async def test_rotas_e_cron_registrados() -> None:
    from app.api.v1.router import api_router
    from app.workers.settings import WorkerSettings

    rotas = {(m, r.path) for r in api_router.routes for m in getattr(r, "methods", set())}
    assert ("GET", "/admin/couriers/{courier_id}/trail") in rotas
    assert ("GET", "/admin/couriers/{courier_id}/trail/deliveries") in rotas
    assert ("GET", "/deliveries/{delivery_id}/trail") in rotas
    assert ("PATCH", "/couriers/{courier_id}/location") in rotas
    assert any(getattr(c, "coroutine", None) is trail.purge_courier_locations for c in WorkerSettings.cron_jobs)


async def test_rastreio_usa_o_ponto_mais_novo_entre_acao_e_rastro(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area, courier, merchant, nbhd = await _base(s)
        d = await _entrega(s, area, courier, merchant, nbhd, state="COLETADA")
        s.add(DeliveryLocation(area_id=area.id, delivery_id=d.id, courier_id=courier.id, action="coletou", lat=-21.54, lng=-42.18, recorded_at=T0 + timedelta(minutes=2)))
        await s.flush()
        p = await trail.ultima_posicao_na_entrega(s, delivery=d)
        assert (p.lat, p.lng) == (-21.54, -42.18)
        # ponto do rastro depois da coleta: passa a ser a posição do rastreio
        s.add(CourierLocation(area_id=area.id, courier_id=courier.id, lat=-21.55, lng=-42.19, recorded_at=T0 + timedelta(minutes=5)))
        # ponto de ANTES do aceite não conta
        s.add(CourierLocation(area_id=area.id, courier_id=courier.id, lat=-21.0, lng=-42.0, recorded_at=T0 - timedelta(minutes=5)))
        await s.flush()
        p = await trail.ultima_posicao_na_entrega(s, delivery=d)
        assert (p.lat, p.lng) == (-21.55, -42.19)


async def test_entregas_recentes_so_com_rastro_pela_mais_recente(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area, courier, merchant, nbhd = await _base(s)
        agora = T0 + timedelta(hours=3)
        feita = await _entrega(
            s, area, courier, merchant, nbhd, state="ENTREGUE",
            accepted_at=T0, delivered_at=T0 + timedelta(minutes=20), token="B",
        )
        ativa = await _entrega(
            s, area, courier, merchant, nbhd, state="COLETADA",
            accepted_at=T0 + timedelta(hours=1), token="C",
        )
        sem_rastro = await _entrega(
            s, area, courier, merchant, nbhd, state="ENTREGUE",
            accepted_at=T0 + timedelta(hours=2), delivered_at=T0 + timedelta(hours=2), token="D",
        )
        pontos = [
            (feita.id, T0 + timedelta(minutes=5)),
            (ativa.id, T0 + timedelta(hours=1, minutes=5)),
            (ativa.id, T0 - timedelta(days=10)),  # fora da retenção: não conta
        ]
        for did, quando in pontos:
            s.add(CourierLocation(
                area_id=area.id, courier_id=courier.id, delivery_id=did,
                lat=-21.54, lng=-42.18, recorded_at=quando,
            ))
        await s.flush()
        out = await trail.entregas_recentes(s, courier=courier, agora=agora)
        assert [e.id for e in out] == [ativa.id, feita.id]
        assert sem_rastro.id not in [e.id for e in out]
        assert out[0].ended_at is None and out[0].merchant_name == "Loja"
        assert out[1].ended_at is not None
        # só o período da primeira entrega
        so_feita = await trail.entregas_recentes(
            s, courier=courier, inicio=T0, fim=T0 + timedelta(minutes=30), agora=agora
        )
        assert [e.id for e in so_feita] == [feita.id]
