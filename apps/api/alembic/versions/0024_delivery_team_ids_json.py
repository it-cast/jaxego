"""Replace delivery.team_id FK with team_ids JSON array. Make courier.team_id NOT NULL."""

from alembic import op
import sqlalchemy as sa

revision = "0024_team_ids_json"
down_revision = "0023_delivery_team_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Deliveries: drop FK + column, add JSON column
    op.drop_constraint("fk_deliveries_team_id", "deliveries", type_="foreignkey")
    op.drop_index("ix_deliveries_team_id", "deliveries")
    op.drop_column("deliveries", "team_id")
    op.add_column("deliveries", sa.Column("team_ids", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("deliveries", "team_ids")
    op.add_column("deliveries", sa.Column("team_id", sa.BigInteger, nullable=True))
    op.create_index("ix_deliveries_team_id", "deliveries", ["team_id"])
    op.create_foreign_key("fk_deliveries_team_id", "deliveries", "teams", ["team_id"], ["id"], ondelete="SET NULL")
