"""Add address_number and address_neighborhood to merchants."""

from alembic import op
import sqlalchemy as sa

revision = "0019_merchant_address_fields"
down_revision = "0018_drop_score_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("merchants", sa.Column("address_number", sa.String(20), nullable=True))
    op.add_column("merchants", sa.Column("address_neighborhood", sa.String(120), nullable=True))


def downgrade() -> None:
    op.drop_column("merchants", "address_neighborhood")
    op.drop_column("merchants", "address_number")
