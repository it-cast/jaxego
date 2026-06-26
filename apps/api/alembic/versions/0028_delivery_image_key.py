"""Add image_key to deliveries for product photo."""

from alembic import op
import sqlalchemy as sa

revision = "0028_delivery_image_key"
down_revision = "0027_team_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("deliveries", sa.Column("image_key", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("deliveries", "image_key")
