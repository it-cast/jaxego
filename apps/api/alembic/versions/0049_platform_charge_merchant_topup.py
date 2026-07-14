"""platform_charges + merchant_credit_ledger ganham colunas pra recarga de saldo

Recarga de saldo (kind="topup") não é amarrada a uma entrega nem a uma
assinatura — precisa de um jeito direto de saber de qual loja é a cobrança
(platform_charges.merchant_id) e de separar o total cobrado no PIX
(amount_cents, já com taxa_pix + taxa_servico somadas) do valor que
efetivamente vira saldo (net_amount_cents — só a recarga, sem as taxas).
merchant_credit_ledger.charge_id é a chave de idempotência do lançamento
"topup" (uma cobrança credita o saldo no máximo uma vez). Mesma convenção de
subscription_id/delivery_id: BIG_ID nullable, indexado, sem FK dura.

Revision ID: 0049
Revises: 0048
Create Date: 2026-07-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0049"
down_revision = "0048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "platform_charges",
        sa.Column("merchant_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "platform_charges",
        sa.Column("net_amount_cents", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_platform_charges_merchant_id", "platform_charges", ["merchant_id"]
    )
    op.add_column(
        "merchant_credit_ledger",
        sa.Column("charge_id", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        "ix_merchant_credit_ledger_charge_id", "merchant_credit_ledger", ["charge_id"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_merchant_credit_ledger_charge_id", table_name="merchant_credit_ledger"
    )
    op.drop_column("merchant_credit_ledger", "charge_id")
    op.drop_index("ix_platform_charges_merchant_id", table_name="platform_charges")
    op.drop_column("platform_charges", "net_amount_cents")
    op.drop_column("platform_charges", "merchant_id")
