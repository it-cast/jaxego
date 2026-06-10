"""Area-scoped base repository (multi-area isolation, layer 2).

Pattern 1 (RESEARCH): the area scope is injected into the WHERE clause of EVERY
domain read/write — never checked in an `if` after the fetch. Domain repositories
inherit from `AreaScopedRepository`; this is the single place the `WHERE area_id`
filter lives. There is no domain-read method that omits `area_id`, so a future
query cannot silently leak across areas (Pitfall 5).

`get_for_area` returns None for a row that belongs to another area, so the caller
raises 404 (not 403) — never leaking that the resource exists elsewhere (A01).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.db.mixins import AreaScopedMixin


class AreaScopedRepository[ModelT: AreaScopedMixin]:
    """Base repository whose reads are structurally scoped to a single area."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, area_id: int) -> Select[tuple[ModelT]]:
        """Build the area-scoped SELECT — the single source of the filter."""
        return select(self.model).where(self.model.area_id == area_id)  # type: ignore[attr-defined]

    async def get_for_area(self, obj_id: int, *, area_id: int) -> ModelT | None:
        """Fetch one row by id within the given area, or None (caller -> 404)."""
        stmt = self._base_select(area_id=area_id).where(self.model.id == obj_id)  # type: ignore[attr-defined]
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_for_area(
        self, *, area_id: int, limit: int = 100, offset: int = 0
    ) -> list[ModelT]:
        """List rows within the given area (no N+1; single query)."""
        stmt = self._base_select(area_id=area_id).limit(limit).offset(offset)
        return list((await self._session.execute(stmt)).scalars().all())
