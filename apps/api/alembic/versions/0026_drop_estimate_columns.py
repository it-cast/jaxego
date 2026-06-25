"""Drop estimate_min_cents and estimate_max_cents from deliveries."""

from alembic import op
import sqlalchemy as sa

revision = "0026_drop_estimate_columns"
down_revision = "0025_delivery_price_cents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("deliveries", "estimate_min_cents")
    op.drop_column("deliveries", "estimate_max_cents")


def downgrade() -> None:
    op.add_column("deliveries", sa.Column("estimate_min_cents", sa.Integer(), nullable=True))
    op.add_column("deliveries", sa.Column("estimate_max_cents", sa.Integer(), nullable=True))
