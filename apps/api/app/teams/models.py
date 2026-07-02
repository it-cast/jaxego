"""Team model — area-scoped equipes managed by area admins."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
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


class TeamZona(Base, AreaScopedMixin, TimestampMixin):
    """Preço mínimo de entrega de um time para uma zona específica."""

    __tablename__ = "team_zonas"
    __table_args__ = (
        UniqueConstraint("team_id", "zona_id", name="uq_team_zonas_team_zona"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("teams.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    zona_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("zonas.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    preco_minimo_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
