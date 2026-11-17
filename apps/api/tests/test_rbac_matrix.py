"""RBAC matrix per endpoint (T-15, REQ-007).

A role without permission gets 403; `require_platform_admin` is a SEPARATE
dependency (A01); `require_role` accepts an exact role or its family prefix.

Desde dd23333 o papel vem da PRÓPRIA conta autenticada (Actor.role: courier | merchant | equipe |
admin_area:<r> | admin_plataforma); não há mais `resolve_role(user, area)` nem vínculos por área.
"""

from __future__ import annotations

import pytest
from app.auth.dependencies import ForbiddenError, require_platform_admin, require_role
from app.auth.principals import Actor


def _actor(actor_type: str, role: str, area_id: int | None = 5) -> Actor:
    return Actor(
        type=actor_type, id=1, area_id=area_id, role=role, email="a@example.com", name="A", row=None
    )


@pytest.mark.asyncio
async def test_require_platform_admin_blocks_non_admin() -> None:
    for a in (
        _actor("area_admin", "admin_area:owner"),
        _actor("merchant", "merchant"),
        _actor("courier", "courier"),
    ):
        with pytest.raises(ForbiddenError):
            await require_platform_admin(a)


@pytest.mark.asyncio
async def test_require_platform_admin_allows_admin() -> None:
    admin = _actor("platform_admin", "admin_plataforma", area_id=None)
    assert await require_platform_admin(admin) is admin


@pytest.mark.asyncio
async def test_require_role_family_prefix_match() -> None:
    """An 'admin_area' allowance matches 'admin_area:owner' (family prefix)."""
    admin = _actor("area_admin", "admin_area:owner")
    dep = require_role("admin_area")
    assert await dep(admin, 5) is admin


@pytest.mark.asyncio
async def test_require_role_exact_match() -> None:
    loja = _actor("merchant", "merchant")
    assert await require_role("merchant")(loja, 5) is loja


@pytest.mark.asyncio
async def test_require_role_denies_missing_role() -> None:
    viewer = _actor("area_admin", "admin_area:viewer")
    with pytest.raises(ForbiddenError):
        await require_role("admin_plataforma")(viewer, 5)


@pytest.mark.asyncio
async def test_require_role_other_actor_types_denied() -> None:
    """Entregador e loja não passam por rota de admin da área."""
    dep = require_role("admin_area")
    for a in (
        _actor("courier", "courier"),
        _actor("merchant", "merchant"),
        _actor("team", "equipe"),
    ):
        with pytest.raises(ForbiddenError):
            await dep(a, 5)
