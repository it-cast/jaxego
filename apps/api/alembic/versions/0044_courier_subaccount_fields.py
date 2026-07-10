"""courier subaccount fields: birth_date, address, bank data, s2p_token

Revision ID: 0044
Revises: 0043
Create Date: 2026-07-10
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0044"
down_revision = "0043"  # noqa: E501
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("couriers", sa.Column("s2p_token", sa.String(100), nullable=True))
    op.add_column("couriers", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("couriers", sa.Column("zip_code", sa.String(8), nullable=True))
    op.add_column("couriers", sa.Column("street", sa.String(200), nullable=True))
    op.add_column("couriers", sa.Column("street_number", sa.String(10), nullable=True))
    op.add_column("couriers", sa.Column("complement", sa.String(60), nullable=True))
    op.add_column("couriers", sa.Column("neighborhood", sa.String(100), nullable=True))
    op.add_column("couriers", sa.Column("city", sa.String(100), nullable=True))
    op.add_column("couriers", sa.Column("state", sa.String(2), nullable=True))
    op.add_column("couriers", sa.Column("bank_code", sa.String(10), nullable=True))
    op.add_column("couriers", sa.Column("bank_agency", sa.String(10), nullable=True))
    op.add_column("couriers", sa.Column("bank_account", sa.String(20), nullable=True))
    op.add_column("couriers", sa.Column("bank_account_digit", sa.String(2), nullable=True))
    op.add_column("couriers", sa.Column("bank_account_type", sa.String(2), nullable=True))


def downgrade() -> None:
    for col in [
        "bank_account_type", "bank_account_digit", "bank_account", "bank_agency",
        "bank_code", "state", "city", "neighborhood", "complement",
        "street_number", "street", "zip_code", "birth_date", "s2p_token",
    ]:
        op.drop_column("couriers", col)
