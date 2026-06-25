"""Add boundary (GeoJSON polygon) to areas."""

from alembic import op
import sqlalchemy as sa

revision = "0020_area_boundary"
down_revision = "0019_merchant_address_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("areas", sa.Column("boundary", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("areas", "boundary")
