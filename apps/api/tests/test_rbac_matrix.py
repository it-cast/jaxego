"""RBAC matrix per endpoint (T-15, REQ-007).

A role without permission gets 403; `require_platform_admin` is a SEPARATE
dependency (A01); `resolve_role` maps (user, area) -> role per context (D-09);
`require_role` accepts an exact role or its family prefix.
"""

from __future__ import annotations

import pytest
from app.areas.service import resolve_role
from app.auth.dependencies import ForbiddenError, require_platform_admin, require_role


class _FakeMembership:
    def __init__(self, area_id: int, role: str) -> None:
        self.area_id = area_id
        self.role = role


class _FakeUser:
    def __init__(self, *, platform_role: str = "user", memberships=None) -> None:
        self.id = 1
        self.platform_role = platform_role
        self._memberships = memberships or []


def test_resolve_role_platform_admin_everywhere() -> None:
    user = _FakeUser(platform_role="admin_plataforma")
    assert resolve_role(user, area_id=99) == "admin_plataforma"  # type: ignore[arg-type]


def test_resolve_role_area_membership() -> None:
    user = _FakeUser(memberships=[_FakeMembership(5, "owner")])
    assert resolve_role(user, area_id=5) == "admin_area:owner"  # type: ignore[arg-type]


def test_resolve_role_other_area_is_user() -> None:
    user = _FakeUser(memberships=[_FakeMembership(5, "owner")])
    assert resolve_role(user, area_id=7) == "user"  # type: ignore[arg-type]


def test_resolve_role_no_membership_is_user() -> None:
    user = _FakeUser()
    assert resolve_role(user, area_id=5) == "user"  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_require_platform_admin_blocks_non_admin() -> None:
    user = _FakeUser(platform_role="user")
    with pytest.raises(ForbiddenError):
        await require_platform_admin(user)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_require_platform_admin_allows_admin() -> None:
    user = _FakeUser(platform_role="admin_plataforma")
    assert await require_platform_admin(user) is user  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_require_role_family_prefix_match() -> None:
    """An 'admin_area' allowance matches 'admin_area:owner' (family prefix)."""
    user = _FakeUser(memberships=[_FakeMembership(5, "owner")])
    dep = require_role("admin_area")
    result = await dep(user, 5)  # type: ignore[arg-type]
    assert result is user


@pytest.mark.asyncio
async def test_require_role_denies_missing_role() -> None:
    user = _FakeUser(memberships=[_FakeMembership(5, "viewer")])
    dep = require_role("admin_plataforma")
    with pytest.raises(ForbiddenError):
        await dep(user, 5)  # type: ignore[arg-type]
