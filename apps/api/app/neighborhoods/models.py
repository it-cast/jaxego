"""Neighborhood model — the per-area catalog the admin curates (D-01/D-02).

`Neighborhood` is AREA-SCOPED (AreaScopedMixin): a neighborhood belongs to exactly
one area. It is valid by NAME alone — the `polygon` is OPTIONAL in M1 (a name-only
neighborhood still routes by name; the polygon unlocks cities of irregular
geography).

The `polygon` column EXISTS in MySQL (added by migration 0005 as
`POLYGON NULL SRID 4326`) but is DELIBERATELY NOT mapped as an ORM attribute
(LOW-1: no GeoAlchemy2). All polygon read/write goes through `func.ST_*` in SQL
Core (see `spatial.py`). On SQLite (tests) the column does not exist at all, so
every spatial assertion is `@pytest.mark.mysql`.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin


class Neighborhood(Base, AreaScopedMixin, TimestampMixin):
    """A catalog neighborhood (D-01). Area-scoped; polygon optional (out of ORM)."""

    __tablename__ = "neighborhoods_catalog"
    __table_args__ = (
        # Catalog lookup by (area, name) — single-query list, no N+1.
        Index("ix_neighborhoods_catalog_area_id_name", "area_id", "name"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # D-01: informal neighborhoods are first-class in the interior.
    is_informal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Soft-archive: removal with active deliveries is blocked → archive instead.
    archived_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)

    # NOTE: the MySQL-only `polygon POLYGON NULL SRID 4326` column is NOT mapped
    # here on purpose (LOW-1). It is read/written exclusively via func.ST_* in
    # spatial.py; mapping a native geometry type would break SQLite create_all.
