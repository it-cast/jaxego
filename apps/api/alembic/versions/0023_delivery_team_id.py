"""Add team_id to deliveries."""

from alembic import op
import sqlalchemy as sa

revision = "0023_delivery_team_id"
down_revision = "0022_courier_team_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("deliveries", sa.Column("team_id", sa.BigInteger, nullable=True))
    op.create_index("ix_deliveries_team_id", "deliveries", ["team_id"])
    op.create_foreign_key(
        "fk_deliveries_team_id",
        "deliveries",
        "teams",
        ["team_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_deliveries_team_id", "deliveries", type_="foreignkey")
    op.drop_index("ix_deliveries_team_id", "deliveries")
    op.drop_column("deliveries", "team_id")
