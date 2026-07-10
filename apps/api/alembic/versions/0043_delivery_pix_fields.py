"""add pix payment columns to deliveries

Revision ID: 0043
Revises: 0042
Create Date: 2026-07-09
"""

from alembic import op
import sqlalchemy as sa

revision = "0043"
down_revision = "0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("deliveries", sa.Column("pix_transaction_id", sa.String(64), nullable=True))
    op.add_column("deliveries", sa.Column("pix_qr_code", sa.Text(), nullable=True))
    op.add_column("deliveries", sa.Column("pix_qr_code_base64", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("deliveries", "pix_qr_code_base64")
    op.drop_column("deliveries", "pix_qr_code")
    op.drop_column("deliveries", "pix_transaction_id")
