"""Fixtures for the payments tests (Phase 10 — Safe2Pay núcleo).

Everything runs against the SQLite in-memory DB (Layer 2 of tests/conftest.py) with
the `PaymentStubAdapter` — the tests NEVER touch the network nor Safe2Pay sandbox
(D-09). The Stub is deterministic: a fixed `IdTransaction`/token, an approved status
by default, and a `scenario` knob ("approved" | "refused" | "down") to drive the
refusal (F-03 E3) and circuit-breaker paths.

`crypto_keys` sets the AES + RSA env so `crypto.py` round-trips; it generates a fresh
RSA-2048 keypair per session and a random 32-byte AES key, and resets the cached
`settings` so the new env is read.

`payments_seed` builds the minimal world: an area, a store owner + Merchant +
Free/paid SubscriptionPlans + a MerchantSubscription, a MEI-approved active courier
with an `s2p_recipient_id`, and two catalog neighborhoods + an online courier so a
delivery can be created and charged with a split.

The MySQL-only acceptance tests (migration 0009 reversible, escrow ledger / charges
constraints) are marked `@pytest.mark.mysql` and skipped in dev via `-m "not mysql"`.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from decimal import Decimal

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.auth.models import User
from app.core.security import hash_password
from app.couriers.models import Courier, CourierCoverageArea, CourierPricingTable
from app.merchants.models import Merchant, MerchantSubscription, MerchantUser
from app.neighborhoods.models import Neighborhood
from app.payments.models import (  # noqa: F401 (registers Phase 10 mappers)
    EscrowLedger,
    PaymentWebhookEvent,
    PlatformCharge,
)
from app.plans.models import SubscriptionPlan
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PASSWORD = "correct-horse-staple-10"


def _rsa_keypair_pem() -> tuple[str, str]:
    """Fresh RSA-2048 keypair as PEM strings (private, public)."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = (
        key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


@pytest.fixture
def crypto_keys(monkeypatch: pytest.MonkeyPatch):
    """Set AES + RSA env and reset cached settings so crypto.py reads them.

    Returns the (private_pem, public_pem) so the RSA-OAEP tests can encrypt with
    the public key exactly as the frontend would.
    """
    aes_hex = os.urandom(32).hex()  # 64 hex chars
    private_pem, public_pem = _rsa_keypair_pem()
    monkeypatch.setenv("SAFE2PAY_TOKEN_ENCRYPT_KEY", aes_hex)
    monkeypatch.setenv("RSA_PRIVATE_KEY", private_pem)
    monkeypatch.setenv("RSA_PUBLIC_KEY", public_pem)

    # Reset the lru_cache'd settings so the new env is picked up.
    from app.core import config as config_mod

    config_mod.get_settings.cache_clear()
    config_mod.settings = config_mod.get_settings()
    # crypto.py reads `settings` at call time via the module attribute.
    import app.payments.crypto as crypto_mod

    crypto_mod.settings = config_mod.settings
    yield (private_pem, public_pem)
    config_mod.get_settings.cache_clear()
    config_mod.settings = config_mod.get_settings()


def rsa_encrypt_for_backend(public_pem: str, plaintext: str) -> str:
    """Encrypt `plaintext` with the RSA public key (what the frontend does)."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    public_key = serialization.load_pem_public_key(public_pem.encode())
    ciphertext = public_key.encrypt(  # type: ignore[union-attr]
        plaintext.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return base64.b64encode(ciphertext).decode()


@pytest.fixture
def payment_stub():
    """A deterministic Stub adapter (no network). Default scenario: approved."""
    from app.payments.safe2pay_stub import PaymentStubAdapter

    return PaymentStubAdapter(scenario="approved")


@pytest_asyncio.fixture
async def auth_payments_client(session_factory, monkeypatch):
    """App client with the webhook secret set + get_session overridden to test DB.

    Used by the webhook ENDPOINT tests (HMAC + dedup). The webhook secret is a
    fixed test value; the signature helper in the test signs with the same value.
    """
    from collections.abc import AsyncIterator

    from app.core import config as config_mod
    from app.db.session import get_session
    from app.main import create_app
    from httpx import ASGITransport, AsyncClient

    monkeypatch.setenv("SAFE2PAY_SECRET_KEY", "test-webhook-secret")
    config_mod.get_settings.cache_clear()
    config_mod.settings = config_mod.get_settings()
    import app.payments.webhooks_router as wh_mod

    wh_mod.settings = config_mod.settings

    async def _override() -> AsyncIterator[AsyncSession]:
        async with session_factory() as s:
            yield s

    application = create_app()
    application.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    application.dependency_overrides.clear()
    config_mod.get_settings.cache_clear()
    config_mod.settings = config_mod.get_settings()


@dataclass
class PaymentsSeed:
    """Seeded world for the payments tests."""

    area_a_id: int
    area_b_id: int
    owner_user_id: int
    merchant_id: int
    free_plan_id: int
    pro_plan_id: int
    subscription_id: int
    courier_id: int  # MEI approved, has s2p_recipient_id
    courier_no_mei_id: int  # mei_pending → no subaccount
    pickup_nbhd_id: int
    dropoff_nbhd_id: int


@pytest_asyncio.fixture
async def payments_seed(session_factory: async_sessionmaker[AsyncSession]) -> PaymentsSeed:
    """Build the minimal world for charge/split/escrow/subscription tests."""
    async with session_factory() as s:
        area_a = Area(codename="padua", name="Pádua", config={})
        area_b = Area(codename="itaocara", name="Itaocara", config={})
        s.add_all([area_a, area_b])
        await s.flush()

        owner = User(
            email="loja@example.com",
            name="Loja Dona",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        s.add(owner)
        await s.flush()

        merchant = Merchant(
            area_id=area_a.id,
            account_type="cnpj",
            document="12345678000190",
            trade_name="Padaria do João",
            category="alimentacao",
            phone_e164="+5522999990001",
            email="loja@example.com",
            status="active",
        )
        s.add(merchant)
        await s.flush()
        s.add(MerchantUser(merchant_id=merchant.id, user_id=owner.id, role="owner"))

        free = SubscriptionPlan(
            code="free",
            name="Free",
            price_cents=0,
            deliveries_per_month=30,
            fee_cents=200,
            is_free=True,
            is_unlimited=False,
            sort_order=0,
        )
        pro = SubscriptionPlan(
            code="pro",
            name="Profissional",
            price_cents=9990,
            deliveries_per_month=300,
            fee_cents=150,
            is_free=False,
            is_unlimited=False,
            sort_order=2,
        )
        s.add_all([free, pro])
        await s.flush()

        sub = MerchantSubscription(
            area_id=area_a.id,
            merchant_id=merchant.id,
            plan_id=free.id,
            status="active",
            billing_status="trial",
            payment_method=None,
        )
        s.add(sub)
        await s.flush()

        pickup = Neighborhood(area_id=area_a.id, name="Centro", is_informal=False)
        dropoff = Neighborhood(area_id=area_a.id, name="Aeroporto", is_informal=False)
        s.add_all([pickup, dropoff])
        await s.flush()

        courier_user = User(
            email="entregador@example.com",
            name="João Entregador",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        courier_user2 = User(
            email="semmei@example.com",
            name="Pedro Sem MEI",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        s.add_all([courier_user, courier_user2])
        await s.flush()

        courier = Courier(
            area_id=area_a.id,
            user_id=courier_user.id,
            cpf="39053344705",
            full_name="João Entregador",
            phone_e164="+5522999990002",
            email="entregador@example.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
            is_online=True,
            mei_cnpj="98765432000100",
            mei_pending=False,
            s2p_recipient_id="recip_courier_1",
        )
        courier_no_mei = Courier(
            area_id=area_a.id,
            user_id=courier_user2.id,
            cpf="11144477735",
            full_name="Pedro Sem MEI",
            phone_e164="+5522999990003",
            email="semmei@example.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
            is_online=True,
            mei_cnpj=None,
            mei_pending=True,
            s2p_recipient_id=None,
        )
        s.add_all([courier, courier_no_mei])
        await s.flush()

        for c in (courier, courier_no_mei):
            for nb in (pickup, dropoff):
                s.add(
                    CourierCoverageArea(
                        area_id=area_a.id,
                        courier_id=c.id,
                        neighborhood_id=nb.id,
                        kind="include",
                    )
                )
            s.add(
                CourierPricingTable(
                    area_id=area_a.id,
                    courier_id=c.id,
                    mode="neighborhood",
                    neighborhood_id=dropoff.id,
                    price=Decimal("10.00"),
                )
            )

        await s.commit()
        return PaymentsSeed(
            area_a_id=area_a.id,
            area_b_id=area_b.id,
            owner_user_id=owner.id,
            merchant_id=merchant.id,
            free_plan_id=free.id,
            pro_plan_id=pro.id,
            subscription_id=sub.id,
            courier_id=courier.id,
            courier_no_mei_id=courier_no_mei.id,
            pickup_nbhd_id=pickup.id,
            dropoff_nbhd_id=dropoff.id,
        )
