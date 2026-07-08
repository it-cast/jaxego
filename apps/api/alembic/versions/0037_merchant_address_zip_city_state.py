"""merchant: add address_zip, address_city, address_state

Revision ID: 0037
Revises: 0036
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa

revision = "0037"
down_revision = "0036_courier_zona_ativo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("merchants", sa.Column("address_zip", sa.String(10), nullable=True))
    op.add_column("merchants", sa.Column("address_city", sa.String(120), nullable=True))
    op.add_column("merchants", sa.Column("address_state", sa.String(2), nullable=True))


def downgrade() -> None:
    op.drop_column("merchants", "address_state")
    op.drop_column("merchants", "address_city")
    op.drop_column("merchants", "address_zip")
