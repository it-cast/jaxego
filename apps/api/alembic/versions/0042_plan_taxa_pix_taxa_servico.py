"""Adiciona taxa_pix_cents e taxa_servico_cents em subscription_plans.

taxa_pix_cents   — taxa cobrada por operação PIX (em centavos).
taxa_servico_cents — taxa de serviço por entrega (substitui fee_cents no CRUD).
fee_cents é mantido no banco para compatibilidade com entregas existentes;
a lógica de despacho migrará para taxa_servico_cents gradualmente.

Revision ID: 0042
Revises: 0041
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscription_plans",
        sa.Column("taxa_pix_cents", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "subscription_plans",
        sa.Column("taxa_servico_cents", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("subscription_plans", "taxa_servico_cents")
    op.drop_column("subscription_plans", "taxa_pix_cents")
