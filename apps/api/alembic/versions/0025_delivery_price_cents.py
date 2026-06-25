"""Add price_cents to deliveries (replaces estimate_min/max in usage)."""

from alembic import op
import sqlalchemy as sa

revision = "0025_delivery_price_cents"
down_revision = "0024_team_ids_json"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("deliveries", sa.Column("price_cents", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("deliveries", "price_cents")
