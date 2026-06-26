"""Team model — area-scoped equipes managed by area admins."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin


class Team(Base, AreaScopedMixin, TimestampMixin):
    """A team within an area — groups couriers for management."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(18), nullable=True)
    razao_social: Mapped[str | None] = mapped_column(String(200), nullable=True)
    responsavel: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    responsavel_cpf: Mapped[str] = mapped_column(String(14), nullable=False, default="")
    responsavel_user_id: Mapped[int | None] = mapped_column(
        BIG_ID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
