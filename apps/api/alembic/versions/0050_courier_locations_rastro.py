"""courier_locations: rastro do entregador (posição periódica, retenção de 7 dias)

Uma linha por envio de posição do app enquanto o entregador está online: a cada
5 min sem entrega, a cada 1 min com entrega ativa (`delivery_id` preenchido).
Serve para o mapa do rastro no admin da área e na loja da entrega. Não é
auditoria permanente (isso é `delivery_locations`): o job diário
`purge_courier_locations` apaga o que passa de `rastro_retencao_dias`.

Revision ID: 0050
Revises: 0049
Create Date: 2026-11-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision = "0050"
down_revision = "0049"
branch_labels = None
depends_on = None


def _dt() -> sa.types.TypeEngine:
    """DATETIME sem fração de segundo no MySQL ("2026-11-18 14:56:39"): o rastro não precisa
    de microssegundos (pontos com no mínimo 20 s de distância)."""
    return sa.DateTime(timezone=True).with_variant(mysql.DATETIME(fsp=0), "mysql")


def upgrade() -> None:
    op.create_table(
        "courier_locations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "area_id",
            sa.BigInteger(),
            sa.ForeignKey("areas.id", ondelete="RESTRICT", onupdate="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "courier_id",
            sa.BigInteger(),
            sa.ForeignKey("couriers.id", ondelete="CASCADE", onupdate="RESTRICT"),
            nullable=False,
        ),
        sa.Column("delivery_id", sa.BigInteger(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("accuracy_m", sa.Float(), nullable=True),
        sa.Column("recorded_at", _dt(), nullable=False),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_courier_locations_area_id", "courier_locations", ["area_id"])
    op.create_index(
        "ix_courier_locations_courier_id_recorded_at",
        "courier_locations",
        ["courier_id", "recorded_at"],
    )
    op.create_index(
        "ix_courier_locations_delivery_id_recorded_at",
        "courier_locations",
        ["delivery_id", "recorded_at"],
    )
    op.create_index("ix_courier_locations_recorded_at", "courier_locations", ["recorded_at"])


def downgrade() -> None:
    op.drop_index("ix_courier_locations_recorded_at", table_name="courier_locations")
    op.drop_index("ix_courier_locations_delivery_id_recorded_at", table_name="courier_locations")
    op.drop_index("ix_courier_locations_courier_id_recorded_at", table_name="courier_locations")
    op.drop_index("ix_courier_locations_area_id", table_name="courier_locations")
    op.drop_table("courier_locations")
