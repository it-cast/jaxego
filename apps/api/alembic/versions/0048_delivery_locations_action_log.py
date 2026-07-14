"""delivery_locations vira log de auditoria de ações do entregador (courier_id + action)

`delivery_locations` deixa de ser um trilho de posição periódica (nunca foi
ligado a nenhuma tela real) e passa a ser um log append-only: uma linha por
ação real do entregador (aceitou, coletou, chegou ao destino, entregou,
recusou) com a localização dele no momento. Mesma proteção de
`delivery_state_transitions` (trigger que rejeita UPDATE/DELETE) — é
histórico de auditoria, não deve ser editável. Tabela estava vazia (o
endpoint de ingest nunca foi chamado por nenhuma tela), então os dois campos
novos entram como NOT NULL sem precisar de backfill.

Revision ID: 0048
Revises: 0047
Create Date: 2026-07-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0048"
down_revision = "0047"
branch_labels = None
depends_on = None

_TRG_NO_UPDATE = (
    "CREATE TRIGGER trg_dl_no_update BEFORE UPDATE ON delivery_locations "
    "FOR EACH ROW SIGNAL SQLSTATE '45000' "
    "SET MESSAGE_TEXT = 'delivery_locations is append-only (audit log)'"
)
_TRG_NO_DELETE = (
    "CREATE TRIGGER trg_dl_no_delete BEFORE DELETE ON delivery_locations "
    "FOR EACH ROW SIGNAL SQLSTATE '45000' "
    "SET MESSAGE_TEXT = 'delivery_locations is append-only (audit log)'"
)


def upgrade() -> None:
    op.add_column(
        "delivery_locations",
        sa.Column(
            "courier_id",
            sa.BigInteger(),
            sa.ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
            nullable=False,
        ),
    )
    op.add_column(
        "delivery_locations",
        sa.Column("action", sa.String(length=32), nullable=False),
    )
    op.create_index(
        "ix_delivery_locations_courier_id", "delivery_locations", ["courier_id"]
    )
    op.create_index(
        "ix_delivery_locations_action", "delivery_locations", ["action"]
    )
    # Retention purge is gone (this is a permanent log now) — drop the index
    # that only existed to back the purge sweep by recorded_at.
    op.drop_index("ix_delivery_locations_recorded_at", table_name="delivery_locations")

    if op.get_bind().dialect.name == "mysql":
        op.execute(_TRG_NO_UPDATE)
        op.execute(_TRG_NO_DELETE)


def downgrade() -> None:
    if op.get_bind().dialect.name == "mysql":
        op.execute("DROP TRIGGER IF EXISTS trg_dl_no_update")
        op.execute("DROP TRIGGER IF EXISTS trg_dl_no_delete")

    op.create_index(
        "ix_delivery_locations_recorded_at", "delivery_locations", ["recorded_at"]
    )
    op.drop_index("ix_delivery_locations_action", table_name="delivery_locations")
    op.drop_index("ix_delivery_locations_courier_id", table_name="delivery_locations")
    op.drop_column("delivery_locations", "action")
    op.drop_column("delivery_locations", "courier_id")
