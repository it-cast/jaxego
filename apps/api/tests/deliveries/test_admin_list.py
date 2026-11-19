"""Lista de entregas do admin da cidade: busca, filtros, contagem por status, detalhe e
isolamento entre cidades."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from app.areas.models import AreaAdmin
from app.core.security import hash_password
from app.deliveries.models import Delivery, DeliveryStateTransition, Recipient

from tests.helpers import bearer, login

SENHA = "correct-horse-staple-10"


def _entrega(
    seed,
    *,
    state,
    token,
    merchant_id=None,
    courier_id=None,
    ref=None,
    area_id=None,
    created_at=None,
    recipient_id=None,
    payment="direct",
):
    d = Delivery(
        area_id=area_id or seed.area_a_id,
        merchant_id=merchant_id or seed.merchant_id,
        courier_id=courier_id,
        recipient_id=recipient_id,
        dropoff_neighborhood_id=seed.dropoff_nbhd_id,
        state=state,
        payment_method=payment,
        pickup_address="Rua da Loja, 1",
        dropoff_address="Rua do Cliente",
        dropoff_number="440",
        price_cents=1000,
        fee_cents=200,
        items_quantity=1,
        reference_number=ref,
        public_token=token.ljust(26, "X"),
        origin="manual",
    )
    if created_at is not None:
        d.created_at = created_at
    return d


@pytest_asyncio.fixture
async def cenario(delivery_seed, session_factory):
    seed = delivery_seed
    async with session_factory() as s:
        s.add_all(
            [
                AreaAdmin(
                    area_id=seed.area_a_id,
                    name="Admin A",
                    email="adm.a@example.com",
                    password_hash=hash_password(SENHA),
                    role="owner",
                ),
                AreaAdmin(
                    area_id=seed.area_b_id,
                    name="Admin B",
                    email="adm.b@example.com",
                    password_hash=hash_password(SENHA),
                    role="owner",
                ),
            ]
        )
        r = Recipient(area_id=seed.area_a_id, name="Maria", phone_e164="+5522988887777")
        s.add(r)
        await s.flush()
        antiga = datetime.now(UTC) - timedelta(days=10)
        d1 = _entrega(seed, state="CRIADA", token="A1", ref="PED-77")
        d2 = _entrega(
            seed, state="ACEITA", token="A2", courier_id=seed.courier_id, recipient_id=r.id
        )
        d3 = _entrega(
            seed, state="FINALIZADA", token="A3", courier_id=seed.courier_id, created_at=antiga
        )
        d4 = _entrega(seed, state="CANCELADA", token="A4", payment="pix")
        outra = _entrega(
            seed,
            state="CRIADA",
            token="B1",
            merchant_id=seed.other_merchant_id,
            area_id=seed.area_b_id,
        )
        s.add_all([d1, d2, d3, d4, outra])
        await s.flush()
        s.add_all(
            [
                DeliveryStateTransition(
                    area_id=seed.area_a_id,
                    delivery_id=d2.id,
                    from_state=None,
                    to_state="CRIADA",
                    created_at=datetime.now(UTC) - timedelta(minutes=5),
                ),
                DeliveryStateTransition(
                    area_id=seed.area_a_id,
                    delivery_id=d2.id,
                    from_state="CRIADA",
                    to_state="ACEITA",
                    actor_type="courier",
                    created_at=datetime.now(UTC),
                ),
            ]
        )
        await s.commit()
        return {"seed": seed, "ids": [d1.id, d2.id, d3.id, d4.id], "outra": outra.id}


async def _token(client, email):
    return (await login(client, email, SENHA, actor="admin"))["access_token"]


@pytest.mark.asyncio
async def test_lista_so_da_cidade_e_conta_por_status(auth_client, cenario):
    t = await _token(auth_client, "adm.a@example.com")
    r = await auth_client.get("/v1/admin/deliveries", headers=bearer(t))
    assert r.status_code == 200, r.text
    body = r.json()
    ids = [i["id"] for i in body["items"]]
    assert sorted(ids) == sorted(cenario["ids"])  # a da outra cidade não aparece
    assert cenario["outra"] not in ids
    assert ids == sorted(ids, reverse=True)  # mais recente primeiro
    assert body["por_estado"] == {"CRIADA": 1, "ACEITA": 1, "FINALIZADA": 1, "CANCELADA": 1}
    item = next(i for i in body["items"] if i["state"] == "ACEITA")
    assert item["merchant_name"] == "Loja do Bairro"
    assert item["courier_name"] == "João Entregador"
    assert item["dropoff_neighborhood"] == "Aldeia"


@pytest.mark.asyncio
async def test_busca_por_numero_e_referencia(auth_client, cenario):
    t = await _token(auth_client, "adm.a@example.com")
    d1 = cenario["ids"][0]
    r = await auth_client.get("/v1/admin/deliveries", params={"q": f"#{d1}"}, headers=bearer(t))
    assert d1 in [i["id"] for i in r.json()["items"]]
    r = await auth_client.get("/v1/admin/deliveries", params={"q": "ped-77"}, headers=bearer(t))
    assert [i["id"] for i in r.json()["items"]] == [d1]
    r = await auth_client.get("/v1/admin/deliveries", params={"q": "joão"}, headers=bearer(t))
    assert {i["state"] for i in r.json()["items"]} == {"ACEITA", "FINALIZADA"}


@pytest.mark.asyncio
async def test_filtros_status_pagamento_e_periodo(auth_client, cenario):
    t = await _token(auth_client, "adm.a@example.com")
    r = await auth_client.get(
        "/v1/admin/deliveries", params={"state": "CRIADA,ACEITA"}, headers=bearer(t)
    )
    body = r.json()
    assert {i["state"] for i in body["items"]} == {"CRIADA", "ACEITA"}
    assert body["total"] == 2
    # a contagem por status ignora o filtro de status (para os atalhos)
    assert sum(body["por_estado"].values()) == 4

    r = await auth_client.get(
        "/v1/admin/deliveries", params={"payment_method": "pix"}, headers=bearer(t)
    )
    assert [i["state"] for i in r.json()["items"]] == ["CANCELADA"]

    inicio = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    r = await auth_client.get("/v1/admin/deliveries", params={"inicio": inicio}, headers=bearer(t))
    assert "FINALIZADA" not in {i["state"] for i in r.json()["items"]}

    r = await auth_client.get(
        "/v1/admin/deliveries", params={"courier_id": cenario["seed"].courier_id}, headers=bearer(t)
    )
    assert r.json()["total"] == 2


@pytest.mark.asyncio
async def test_paginacao(auth_client, cenario):
    t = await _token(auth_client, "adm.a@example.com")
    r = await auth_client.get(
        "/v1/admin/deliveries", params={"limit": 3, "offset": 3}, headers=bearer(t)
    )
    body = r.json()
    assert body["total"] == 4 and len(body["items"]) == 1


@pytest.mark.asyncio
async def test_detalhe_com_historico_e_telefone_mascarado(auth_client, cenario):
    t = await _token(auth_client, "adm.a@example.com")
    d2 = cenario["ids"][1]
    r = await auth_client.get(f"/v1/admin/deliveries/{d2}", headers=bearer(t))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["recipient_name"] == "Maria"
    assert "88887777" not in (body["recipient_phone_masked"] or "")
    assert [h["to_state"] for h in body["historico"]] == ["CRIADA", "ACEITA"]


@pytest.mark.asyncio
async def test_entrega_de_outra_cidade_da_404(auth_client, cenario):
    t = await _token(auth_client, "adm.b@example.com")
    r = await auth_client.get(f"/v1/admin/deliveries/{cenario['ids'][0]}", headers=bearer(t))
    assert r.status_code == 404
    r = await auth_client.get("/v1/admin/deliveries", headers=bearer(t))
    assert [i["id"] for i in r.json()["items"]] == [cenario["outra"]]


@pytest.mark.asyncio
async def test_filtros_lista_lojas_e_entregadores_da_cidade(auth_client, cenario):
    t = await _token(auth_client, "adm.a@example.com")
    r = await auth_client.get("/v1/admin/deliveries/filtros", headers=bearer(t))
    body = r.json()
    assert [loja["nome"] for loja in body["lojas"]] == ["Loja do Bairro"]
    assert [e["nome"] for e in body["entregadores"]] == ["João Entregador"]


@pytest.mark.asyncio
async def test_loja_nao_acessa(auth_client, cenario):
    t = (await login(auth_client, "loja@example.com", SENHA, actor="loja"))["access_token"]
    r = await auth_client.get("/v1/admin/deliveries", headers=bearer(t))
    assert r.status_code == 403
