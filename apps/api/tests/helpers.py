"""Importable test helpers (dataclasses + login/bearer utilities).

Kept out of conftest so test modules can `from tests.helpers import ...`
(conftest is a pytest plugin, not a normal importable module).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.areas.models import Area
from app.auth.models import User
from httpx import AsyncClient


@dataclass
class Seed:
    """Seeded entities for isolation/RBAC tests."""

    area_a: Area
    area_b: Area
    admin_a: User
    admin_b: User
    platform_admin: User
    password: str


async def login(client: AsyncClient, email: str, password: str, totp: str | None = None) -> dict:
    """POST /v1/auth/login and return the JSON body (raises on non-200)."""
    payload: dict = {"email": email, "password": password}
    if totp is not None:
        payload["totp"] = totp
    resp = await client.post("/v1/auth/login", json=payload)
    resp.raise_for_status()
    return resp.json()


def bearer(token: str) -> dict[str, str]:
    """Authorization header for an access token."""
    return {"Authorization": f"Bearer {token}"}
