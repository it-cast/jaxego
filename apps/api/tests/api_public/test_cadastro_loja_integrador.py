"""Cadastro da loja pelo integrador (Menu Certo) e acesso da loja — escopo merchants:write.

SQLite em memória (conftest). A loja nasce ativa, no plano pedido, com a assinatura
paga pelo integrador (billing_status active, sem forma de pagamento: nenhum job cobra);
desligar = "cancelado" (a guarda de criação de entrega barra e o sync de inadimplência
não religa); religar = "active". Loja de outra área = 404.
"""

from __future__ import annotations

import pytest
from app.api_keys.schemas import ALLOWED_SCOPES
from app.api_public import service
from app.api_public.schemas import PublicCreateMerchantBody
from app.areas.models import Area
from app.audit.models import AuditLog
from app.core.exceptions import AppError
from app.integrations.geocoding_stub import GeocodingStubAdapter
from app.integrations.receita_stub import ReceitaStubAdapter
from app.merchants.models import Merchant, MerchantSubscription
from app.payments.subscriptions import (
    SubscriptionBlockedError,
    assert_subscription_active,
    sync_delinquency,
)
from app.plans.models import SubscriptionPlan
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.asyncio

CORPO = {
    "account_type": "cpf",
    "document": "182.959.417-63",
    "trade_name": "Goyer's Beer",
    "category": "restaurante",
    "phone_e164": "+5522999990000",
    "email": "loja@example.com",
    "password": "jaxego1234",
    "plan_code": "pro",
    "consent": True,
    "external_ref": "menucerto-809",
    "address": "Rua A",
    "address_number": "10",
    "address_neighborhood": "Centro",
    "address_zip": "28470000",
    "address_state": "RJ",
    "lat": -21.53,
    "lng": -42.18,
}


async def _base(s: AsyncSession) -> tuple[Area, Area]:
    a = Area(codename="padua", name="Pádua", config={})
    b = Area(codename="itaocara", name="Itaocara", config={})
    s.add_all(
        [
            a,
            b,
            SubscriptionPlan(code="free", name="Básico", is_free=True),
            SubscriptionPlan(code="pro", name="Pro", price_monthly_cents=2990),
        ]
    )
    await s.flush()
    return a, b


async def _criar(s: AsyncSession, area_id: int, **extra) -> object:
    return await service.create_merchant_by_integrator(
        s,
        area_id=area_id,
        body=PublicCreateMerchantBody.model_validate({**CORPO, **extra}),
        receita=ReceitaStubAdapter("ativa"),
        geocoding=GeocodingStubAdapter(scenario="padua"),
        ip="127.0.0.1",
        api_key_id=7,
    )


async def test_escopo_novo_e_consentimento_obrigatorio() -> None:
    assert "merchants:write" in ALLOWED_SCOPES
    with pytest.raises(ValueError):
        PublicCreateMerchantBody.model_validate({**CORPO, "consent": False})
    with pytest.raises(ValueError):
        PublicCreateMerchantBody.model_validate({**CORPO, "password": "curta"})
    with pytest.raises(ValueError):
        PublicCreateMerchantBody.model_validate({**CORPO, "status": "active"})


async def test_cria_loja_ativa_no_plano_pago_pelo_integrador(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area, _ = await _base(s)
        out = await _criar(s, area.id)
        await s.commit()
        assert (out.status, out.plan_code, out.access) == ("active", "pro", "active")

        m = await s.get(Merchant, out.merchant_id)
        assert (m.area_id, m.document, m.external_ref) == (area.id, "18295941763", "menucerto-809")
        assert m.password_hash and m.password_hash != "jaxego1234"
        sub = (
            await s.execute(select(MerchantSubscription).where(MerchantSubscription.merchant_id == m.id))
        ).scalar_one()
        pro = (await s.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == "pro"))).scalar_one()
        assert (sub.plan_id, sub.billing_status, sub.payment_method, sub.due_at, sub.amount_cents) == (
            pro.id,
            "active",
            None,
            None,
            0,
        )
        acoes = (await s.execute(select(AuditLog.action))).scalars().all()
        assert "merchant.created_by_integrator" in acoes

        # Mesmo documento de novo: conta duplicada (o integrador então resolve pelo documento)
        with pytest.raises(AppError) as e:
            await _criar(s, area.id, email="outra@example.com", phone_e164="+5522988887777")
        assert e.value.code == "duplicate_account"


async def test_receita_fora_do_ar_nao_deixa_esperando_e_plano_inexistente(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area, _ = await _base(s)
        out = await service.create_merchant_by_integrator(
            s,
            area_id=area.id,
            body=PublicCreateMerchantBody.model_validate(
                {**CORPO, "account_type": "cnpj", "document": "11.222.333/0001-81"}
            ),
            receita=ReceitaStubAdapter("down"),
            geocoding=GeocodingStubAdapter(scenario="padua"),
            ip=None,
            api_key_id=7,
        )
        m = await s.get(Merchant, out.merchant_id)
        assert (m.status, m.next_revalidation_at) == ("active", None)

        with pytest.raises(AppError) as e:
            await _criar(s, area.id, plan_code="ouro", document="79280435051", email="x@example.com", phone_e164="+5522977776666")
        assert e.value.code == "plan_not_found"


async def test_desliga_e_religa_o_acesso_e_o_sync_nao_religa(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area, outra = await _base(s)
        out = await _criar(s, area.id)
        await s.commit()
        mid = out.merchant_id

        r = await service.set_merchant_access(s, area_id=area.id, merchant_id=mid, active=False, ip=None, api_key_id=7)
        await s.commit()
        assert (r.access, r.billing_status) == ("disabled", "cancelado")
        with pytest.raises(SubscriptionBlockedError):
            await assert_subscription_active(s, merchant_id=mid, area_id=area.id)

    # O job de inadimplência não mexe em "cancelado" (só active/blocked)
    await sync_delinquency(session_factory)
    async with session_factory() as s:
        sub = (await s.execute(select(MerchantSubscription).where(MerchantSubscription.merchant_id == mid))).scalar_one()
        assert sub.billing_status == "cancelado"

        r = await service.set_merchant_access(s, area_id=area.id, merchant_id=mid, active=True, ip=None, api_key_id=7)
        await s.commit()
        assert (r.access, r.billing_status) == ("active", "active")
        await assert_subscription_active(s, merchant_id=mid, area_id=area.id)

        # Loja de outra área: 404, sem vazar existência
        with pytest.raises(AppError) as e:
            await service.set_merchant_access(s, area_id=outra.id, merchant_id=mid, active=False, ip=None, api_key_id=7)
        assert e.value.status_code == 404
        acoes = (await s.execute(select(AuditLog.action))).scalars().all()
        assert acoes.count("merchant.access_by_integrator") == 2
