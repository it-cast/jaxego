"""Add team_id to couriers."""

from alembic import op
import sqlalchemy as sa

revision = "0022_courier_team_id"
down_revision = "0021_teams"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("couriers", sa.Column("team_id", sa.BigInteger, nullable=True))
    op.create_index("ix_couriers_team_id", "couriers", ["team_id"])
    op.create_foreign_key(
        "fk_couriers_team_id",
        "couriers",
        "teams",
        ["team_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_couriers_team_id", "couriers", type_="foreignkey")
    op.drop_index("ix_couriers_team_id", "couriers")
    op.drop_column("couriers", "team_id")
