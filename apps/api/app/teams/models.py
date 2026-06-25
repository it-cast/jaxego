"""Team model — area-scoped equipes managed by area admins."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin


class Team(Base, AreaScopedMixin, TimestampMixin):
    """A team within an area — groups couriers for management."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
