"""Principal (ator autenticado) — substitui o antigo `User` global.

Cada tipo de acesso autentica na própria tabela (couriers, merchants, teams,
area_admins, platform_admins). `Actor` é o objeto que os endpoints recebem via
`CurrentUser`: carrega tipo, id (na tabela do tipo), escopo de área, role e a
linha ORM (`row`) para quem precisa dos campos específicos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import (
    ACTOR_AREA_ADMIN,
    ACTOR_COURIER,
    ACTOR_MERCHANT,
    ACTOR_PLATFORM_ADMIN,
    ACTOR_TEAM,
    PlatformAdmin,
)

PLATFORM_ADMIN_ROLE = "admin_plataforma"


@dataclass
class Actor:
    """Identidade autenticada de qualquer tipo de conta."""

    type: str  # courier | merchant | team | area_admin | platform_admin
    id: int  # id na tabela do tipo
    area_id: int | None  # None para platform_admin (bypass auditado)
    role: str  # courier | merchant | equipe | admin_area:<r> | admin_plataforma
    email: str
    name: str
    row: Any  # instância ORM (Courier | Merchant | Team | AreaAdmin | PlatformAdmin)

    @property
    def platform_role(self) -> str:
        """Compat: 'admin_plataforma' para admin do sistema, 'user' para o resto."""
        return PLATFORM_ADMIN_ROLE if self.type == ACTOR_PLATFORM_ADMIN else "user"

    @property
    def is_active(self) -> bool:
        return bool(getattr(self.row, "is_active", True))


def _model_for(actor_type: str) -> type:
    """Tabela ORM de cada tipo de ator (import tardio evita ciclos)."""
    if actor_type == ACTOR_COURIER:
        from app.couriers.models import Courier

        return Courier
    if actor_type == ACTOR_MERCHANT:
        from app.merchants.models import Merchant

        return Merchant
    if actor_type == ACTOR_TEAM:
        from app.teams.models import Team

        return Team
    if actor_type == ACTOR_AREA_ADMIN:
        from app.areas.models import AreaAdmin

        return AreaAdmin
    if actor_type == ACTOR_PLATFORM_ADMIN:
        return PlatformAdmin
    raise ValueError(f"actor_type desconhecido: {actor_type}")


def build_actor(actor_type: str, row: Any) -> Actor:
    """Monta o Actor a partir da linha ORM do tipo."""
    if actor_type == ACTOR_COURIER:
        return Actor(
            type=actor_type,
            id=row.id,
            area_id=row.area_id,
            role="courier",
            email=row.email,
            name=row.full_name,
            row=row,
        )
    if actor_type == ACTOR_MERCHANT:
        return Actor(
            type=actor_type,
            id=row.id,
            area_id=row.area_id,
            role="merchant",
            email=row.email,
            name=row.trade_name,
            row=row,
        )
    if actor_type == ACTOR_TEAM:
        return Actor(
            type=actor_type,
            id=row.id,
            area_id=row.area_id,
            role="equipe",
            email=row.email or "",
            name=row.name,
            row=row,
        )
    if actor_type == ACTOR_AREA_ADMIN:
        return Actor(
            type=actor_type,
            id=row.id,
            area_id=row.area_id,
            role=f"admin_area:{row.role}",
            email=row.email or "",
            name=row.name,
            row=row,
        )
    if actor_type == ACTOR_PLATFORM_ADMIN:
        return Actor(
            type=actor_type,
            id=row.id,
            area_id=None,
            role=PLATFORM_ADMIN_ROLE,
            email=row.email,
            name=row.name,
            row=row,
        )
    raise ValueError(f"actor_type desconhecido: {actor_type}")


async def load_actor(
    session: AsyncSession, *, actor_type: str, actor_id: int
) -> Actor | None:
    """Carrega o ator pelo (tipo, id) do token. None se não existe/inativo."""
    model = _model_for(actor_type)
    row = await session.get(model, actor_id)
    if row is None:
        return None
    if not bool(getattr(row, "is_active", True)):
        return None
    if getattr(row, "deleted_at", None) is not None:
        return None
    return build_actor(actor_type, row)
