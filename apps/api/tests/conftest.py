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

# Import every model so Base.metadata is complete before create_all.
import importlib
import pkgutil
from collections.abc import AsyncIterator

import app as _app_pkg
import pytest
import pytest_asyncio
from app.areas.models import Area, AreaAdmin
from app.auth.models import PlatformAdmin, RefreshToken  # noqa: F401
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_session
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from tests.helpers import Seed

# Registra TODOS os mappers (app/<módulo>/models.py) antes do create_all: importar por nome
# quebrava a cada modelo removido/renomeado (ex.: User e MerchantUser saíram em dd23333).
for _mod in (m for m in pkgutil.iter_modules(_app_pkg.__path__) if m.ispkg):
    _nome = f"app.{_mod.name}.models"
    try:
        importlib.import_module(_nome)
    except ModuleNotFoundError as _e:
        if _e.name != _nome:
            raise


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

        # Desde dd23333 não há tabela `users`: cada ator tem a sua conta
        # (aqui, admin da área e admin da plataforma)
        admin_a = AreaAdmin(
            area_id=area_a.id,
            name="Admin A",
            email="admin.a@example.com",
            password_hash=pwd_hash,
            role="owner",
        )
        admin_b = AreaAdmin(
            area_id=area_b.id,
            name="Admin B",
            email="admin.b@example.com",
            password_hash=pwd_hash,
            role="owner",
        )
        platform_admin = PlatformAdmin(
            email="platform@example.com", name="Platform", password_hash=pwd_hash
        )
        s.add_all([admin_a, admin_b, platform_admin])
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
