"""Create teams table."""

from alembic import op
import sqlalchemy as sa

revision = "0021_teams"
down_revision = "0020_area_boundary"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("area_id", sa.BigInteger, sa.ForeignKey("areas.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("teams")
