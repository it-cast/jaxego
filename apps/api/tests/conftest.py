"""Shared test fixtures.

Two layers:
1. `app` / `client` — the real app via ASGITransport (used by the health tests;
   datastore checks are mocked per-test).
2. DB-backed fixtures — an in-memory SQLite engine with the full Phase 2 schema
   created from metadata, a session, a seed of 2 areas + 2 area admins + a
   platform admin, and an `auth_client` whose `get_session` is overridden to the
   test session. These let the auth/area tests run WITHOUT live MySQL.

The MySQL-only acceptance test (append-only trigger) is marked `@pytest.mark.mysql`
and skipped here; it runs against MySQL 8 in CI.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

# Import every model so Base.metadata is complete before create_all.
from app.ai.models import AiUsageLog  # noqa: F401 (registers mapper — Phase 14)
from app.api_keys.models import (  # noqa: F401 (registers mappers — Phase 12)
    ApiIdempotencyKey,
    ApiKey,
)
from app.areas.models import Area, AreaAdmin
from app.audit.models import AuditLog  # noqa: F401 (registers mapper)
from app.auth.models import RefreshToken, User  # noqa: F401
from app.core.security import hash_password
from app.couriers.models import (  # noqa: F401 (registers mappers — Phase 5/6)
    Courier,
    CourierCoverageArea,
    CourierDocument,
    CourierPricingTable,
)
from app.db.base import Base
from app.db.session import get_session
from app.deliveries.models import (  # noqa: F401 (registers mappers — Phase 7)
    Delivery,
    DeliveryStateTransition,
    Recipient,
)
from app.merchants.models import (  # noqa: F401 (registers mappers — Phase 4)
    Merchant,
    MerchantSubscription,
    MerchantUser,
)
from app.neighborhoods.models import Neighborhood  # noqa: F401 (Phase 6 mapper)
from app.notifications.models import (  # noqa: F401 (Phase 9 mappers)
    Notification,
    PushSubscription,
)
from app.invoices.models import (  # noqa: F401 (Phase 15 mappers)
    InvoiceLineItem,
    PlatformInvoice,
)
from app.payments.models import (  # noqa: F401 (Phase 10 mappers)
    EscrowLedger,
    PaymentWebhookEvent,
    PlatformCharge,
)
from app.payments_direct.models import (  # noqa: F401 (Phase 9/15 mappers)
    DirectPaymentConfirmation,
    DisputeBlock,
    PaymentDispute,
)
from app.withdrawals.models import Withdrawal  # noqa: F401 (Phase 15 mapper)
from app.plans.models import SubscriptionPlan  # noqa: F401
from app.proofs.models import DeliveryProof  # noqa: F401 (Phase 9 mapper)
from app.ratings.models import CourierRating  # noqa: F401 (Phase 13 mapper)
from app.scores.models import (  # noqa: F401 (Phase 13 mappers)
    CourierScoreSnapshot,
    ScoreWeight,
)
from app.suspensions.models import (  # noqa: F401 (Phase 13 mappers)
    AreaRevenueShare,
    SuspensionAppeal,
)
from app.tracking.models import DeliveryLocation  # noqa: F401 (Phase 9 mapper)
from app.webhooks.models import (  # noqa: F401 (registers mappers — Phase 12)
    WebhookDelivery,
    WebhookEndpoint,
)
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from tests.helpers import Seed


# --- Layer 1: real app + ASGI client (health tests) ---
@pytest.fixture
def app() -> FastAPI:
    """Build a fresh app via the factory."""
    from app.main import create_app

    return create_app()


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Async HTTP client wired to the ASGI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# --- Layer 2: DB-backed fixtures (auth/area tests, SQLite in-memory) ---
@pytest_asyncio.fixture
async def db_engine():
    """In-memory SQLite engine with the full Phase 2 schema.

    StaticPool + a single shared connection so every session sees the same
    in-memory database (otherwise each connection gets a fresh empty DB).
    """
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(db_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=db_engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture
async def db_session(session_factory) -> AsyncIterator[AsyncSession]:
    async with session_factory() as s:
        yield s


@pytest_asyncio.fixture
async def seed(session_factory) -> Seed:
    """Seed 2 areas, 1 area admin each, and a platform admin."""
    password = "correct-horse-staple-10"
    pwd_hash = hash_password(password)
    async with session_factory() as s:
        area_a = Area(codename="padua", name="Pádua", config={})
        area_b = Area(codename="itaocara", name="Itaocara", config={})
        s.add_all([area_a, area_b])
        await s.flush()

        admin_a = User(
            email="admin.a@example.com",
            name="Admin A",
            password_hash=pwd_hash,
            platform_role="user",
        )
        admin_b = User(
            email="admin.b@example.com",
            name="Admin B",
            password_hash=pwd_hash,
            platform_role="user",
        )
        platform_admin = User(
            email="platform@example.com",
            name="Platform",
            password_hash=pwd_hash,
            platform_role="admin_plataforma",
        )
        s.add_all([admin_a, admin_b, platform_admin])
        await s.flush()

        s.add_all(
            [
                AreaAdmin(area_id=area_a.id, user_id=admin_a.id, role="owner"),
                AreaAdmin(area_id=area_b.id, user_id=admin_b.id, role="owner"),
            ]
        )
        await s.commit()

        for obj in (area_a, area_b, admin_a, admin_b, platform_admin):
            await s.refresh(obj)
        return Seed(
            area_a=area_a,
            area_b=area_b,
            admin_a=admin_a,
            admin_b=admin_b,
            platform_admin=platform_admin,
            password=password,
        )


# --- Phase 4: external-integration STUB fixtures (no network — Pitfall 1) ---
@pytest.fixture
def geocoding_stub_padua():
    """Geocoder that always resolves inside the Pádua area."""
    from app.integrations.geocoding_stub import GeocodingStubAdapter

    return GeocodingStubAdapter(scenario="padua")


@pytest.fixture
def geocoding_stub_fora():
    """Geocoder that resolves to a point with no covering area (empty state)."""
    from app.integrations.geocoding_stub import GeocodingStubAdapter

    return GeocodingStubAdapter(scenario="fora")


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear the in-process signup limiter between tests (deterministic)."""
    from app.core.ratelimit import signup_limiter

    signup_limiter.reset()
    yield
    signup_limiter.reset()


@pytest_asyncio.fixture
async def auth_client(session_factory) -> AsyncIterator[AsyncClient]:
    """App client whose get_session yields the test SQLite session."""
    from app.main import create_app

    async def _override() -> AsyncIterator[AsyncSession]:
        async with session_factory() as s:
            yield s

    application = create_app()
    application.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    application.dependency_overrides.clear()
