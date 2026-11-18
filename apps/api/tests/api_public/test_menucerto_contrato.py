"""Contrato da API pública usado pelo Menu Certo (vínculo, cotação, consulta, cancelamento).

Testes sem banco (rodam com `--noconftest`): schema aceita o corpo que o painel monta,
bairro casado por nome sem acento/caixa, documento só por dígitos, equipe opcional na
criação, link de rastreio, regra de cancelamento (RN-019), `delivery_id` no webhook e as
rotas montadas em /v1/public.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.api_public import service
from app.api_public.schemas import PublicCreateDeliveryBody, PublicDeliveryResponse, ResolveMerchantBody
from app.core.exceptions import AppError
from app.webhooks.serializer import serialize_webhook

# O corpo exatamente como o painel do Menu Certo monta (jaxego.service.ts → corpoEntrega)
CORPO_PAINEL = {
    "merchant_id": 42,
    "pickup_address": "Rua A, 10",
    "pickup_neighborhood": "Centro",
    "pickup_lat": -21.5389,
    "pickup_lng": -42.1789,
    "dropoff_neighborhood_name": "São Félix",
    "dropoff_address": "Rua B",
    "dropoff_number": "20",
    "dropoff_complement": "Casa",
    "dropoff_reference": "Perto da praça",
    "cep": "28470000",
    "recipient_name": "Maria Silva",
    "recipient_phone_e164": "+5522999990000",
    "items_description": "Pedido Menu Certo #123",
    "items_quantity": 2,
    "declared_value_cents": 5490,
    "reference_number": "123",
    "notes": "COBRAR NA ENTREGA: R$ 54,90 — Dinheiro.",
    "proof_method": "photo",
    "payment_method": "direct",
}


class _Resultado:
    def __init__(self, itens):
        self._itens = list(itens)

    def scalars(self):
        return self

    def all(self):
        return self._itens

    def first(self):
        return self._itens[0] if self._itens else None


class _SessaoFalsa:
    """Devolve sempre a mesma lista: o filtro por área/arquivado é do SQL, aqui só o casamento.
    A consulta da assinatura (acesso da loja) devolve `assinaturas`."""

    def __init__(self, itens, assinaturas=()):
        self.itens = itens
        self.assinaturas = list(assinaturas)

    async def execute(self, stmt):
        from app.merchants.models import MerchantSubscription

        entidade = stmt.column_descriptions[0].get("entity")
        return _Resultado(self.assinaturas if entidade is MerchantSubscription else self.itens)


def test_schema_aceita_o_corpo_do_painel():
    body = PublicCreateDeliveryBody.model_validate(CORPO_PAINEL)
    assert body.dropoff_neighborhood_id is None
    assert body.dropoff_neighborhood_name == "São Félix"
    assert (body.dropoff_lat, body.pickup_lat) == (None, -21.5389)


def test_schema_exige_bairro_e_coordenadas_em_par():
    sem_bairro = {k: v for k, v in CORPO_PAINEL.items() if k != "dropoff_neighborhood_name"}
    with pytest.raises(ValueError):
        PublicCreateDeliveryBody.model_validate(sem_bairro)
    with pytest.raises(ValueError):
        PublicCreateDeliveryBody.model_validate({**CORPO_PAINEL, "dropoff_lat": -21.5})
    with pytest.raises(ValueError):  # campo desconhecido continua barrado (extra='forbid')
        PublicCreateDeliveryBody.model_validate({**CORPO_PAINEL, "price_cents": 1})


def test_corpo_interno_sem_equipe_com_coordenadas_e_cep_so_digitos():
    body = PublicCreateDeliveryBody.model_validate({**CORPO_PAINEL, "cep": "28470-000", "dropoff_lat": -21.54, "dropoff_lng": -42.18})
    interno = service._to_internal_body(body, dropoff_neighborhood_id=3)
    assert interno.team_ids is None
    assert interno.dropoff_neighborhood_id == 3
    assert (interno.pickup_lat, interno.dropoff_lat, interno.dropoff_lng) == (-21.5389, -21.54, -42.18)
    assert interno.cep == "28470000"
    assert interno.dropoff_reference == "Perto da praça"


def test_normalizar_nome():
    assert service.normalizar_nome("  São   Félix ") == "sao felix"
    assert service.normalizar_nome("GLÓRIA") == service.normalizar_nome("gloria")
    assert service.normalizar_nome(None) == ""


@pytest.mark.asyncio
async def test_bairro_por_nome_sem_acento_formal_antes_do_informal():
    catalogo = [
        SimpleNamespace(id=9, name="Sao Felix", is_informal=True),
        SimpleNamespace(id=3, name="São Félix", is_informal=False),
        SimpleNamespace(id=4, name="Centro", is_informal=False),
    ]
    n = await service.resolve_neighborhood(_SessaoFalsa(catalogo), area_id=1, nbhd_id=None, nome="sao FELIX")
    assert n.id == 3
    with pytest.raises(AppError) as e:
        await service.resolve_neighborhood(_SessaoFalsa(catalogo), area_id=1, nbhd_id=None, nome="Bairro Inexistente")
    assert e.value.code == "neighborhood_not_found"
    assert e.value.status_code == 422


@pytest.mark.asyncio
async def test_loja_pelo_documento_so_digitos_e_status():
    lojas = [
        SimpleNamespace(id=6, document="792.804.350-51", trade_name="Império", status="active", external_ref=None, is_active=True),
        SimpleNamespace(id=42, document="18295941763", trade_name="Loja do Roger", status="active", external_ref="mc-809", is_active=True),
        SimpleNamespace(id=50, document="11222333000181", trade_name="Desligada", status="active", external_ref=None, is_active=False),
    ]
    out = await service.resolve_merchant_by_document(_SessaoFalsa(lojas), area_id=1, document="182.959.417-63")
    assert (out.merchant_id, out.trade_name, out.external_ref) == (42, "Loja do Roger", "mc-809")
    out2 = await service.resolve_merchant_by_document(_SessaoFalsa(lojas), area_id=1, document="79280435051")
    assert out2.merchant_id == 6
    assert out.access == "active"  # sem assinatura = acesso normal
    cancelada = _SessaoFalsa(lojas, [SimpleNamespace(billing_status="cancelado")])
    assert (await service.resolve_merchant_by_document(cancelada, area_id=1, document="18295941763")).access == "disabled"
    assert (await service.resolve_merchant_by_document(_SessaoFalsa(lojas), area_id=1, document="11.222.333/0001-81")).status == "inactive"
    with pytest.raises(AppError) as e:
        await service.resolve_merchant_by_document(_SessaoFalsa(lojas), area_id=1, document="00000000000")
    assert e.value.status_code == 404
    assert ResolveMerchantBody(document="18295941763").document == "18295941763"


def test_cancelavel_so_antes_do_aceite():
    for estado in ("AGENDADA", "AGUARDANDO_PAGAMENTO", "CRIADA", "SEM_RESPOSTA"):
        assert service.cancelavel(estado), estado
    for estado in ("ACEITA", "COLETADA", "ENTREGUE", "RECUSADA_NO_DESTINO", "CANCELADA", "FINALIZADA"):
        assert not service.cancelavel(estado), estado


def test_link_de_rastreio(monkeypatch):
    from app.core import config

    monkeypatch.setattr(config, "get_settings", lambda: SimpleNamespace(public_web_base_url="https://app.jaxego.com.br/"))
    assert service.tracking_url("TOK123") == "https://app.jaxego.com.br/r/TOK123"
    monkeypatch.setattr(config, "get_settings", lambda: SimpleNamespace(public_web_base_url=None))
    assert service.tracking_url("TOK123") is None
    # snapshot de idempotência gravado antes do campo continua válido
    antigo = PublicDeliveryResponse.model_validate({"delivery_id": 1, "public_token": "t", "state": "CRIADA", "fee_cents": 0, "no_couriers_warning": False})
    assert antigo.tracking_url is None


def test_webhook_leva_delivery_id_sem_dado_do_destinatario():
    payload = serialize_webhook(
        event_id="evt1", event_type="delivery.accepted", occurred_at="2026-11-17T10:00:00+00:00",
        public_token="TOK", delivery_id=77, reference_number="123", state="ACEITA",
        dropoff_neighborhood_id=3, dropoff_address="Rua B", dropoff_number="20", dropoff_complement=None,
    )
    assert payload["data"]["delivery_id"] == 77
    assert payload["data"]["dropoff"] == {"neighborhood_id": 3}  # endereço só depois da coleta (RN-013)
    assert "recipient_phone" not in str(payload)


def test_rotas_montadas_em_v1_public():
    from app.api.v1.router import api_router

    rotas = {(m, r.path) for r in api_router.routes for m in getattr(r, "methods", set())}
    for esperado in [
        ("POST", "/public/deliveries"),
        ("GET", "/public/deliveries/{delivery_id}"),
        ("POST", "/public/deliveries/{delivery_id}/cancel"),
        ("POST", "/public/merchants/resolve"),
        ("POST", "/public/merchants"),
        ("POST", "/public/merchants/{merchant_id}/access"),
        ("GET", "/public/quote"),
    ]:
        assert esperado in rotas, esperado
