"""Add cnpj, razao_social, responsavel, responsavel_cpf, responsavel_user_id to teams."""

from alembic import op
import sqlalchemy as sa

revision = "0027_team_fields"
down_revision = "0026_drop_estimate_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("teams", sa.Column("cnpj", sa.String(18), nullable=True))
    op.add_column("teams", sa.Column("razao_social", sa.String(200), nullable=True))
    op.add_column("teams", sa.Column("responsavel", sa.String(120), nullable=False, server_default=""))
    op.add_column("teams", sa.Column("responsavel_cpf", sa.String(14), nullable=False, server_default=""))
    op.add_column("teams", sa.Column("responsavel_user_id", sa.BigInteger, nullable=True))
    op.create_foreign_key("fk_teams_responsavel_user_id", "teams", "users", ["responsavel_user_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_teams_responsavel_user_id", "teams", type_="foreignkey")
    op.drop_column("teams", "responsavel_user_id")
    op.drop_column("teams", "responsavel_cpf")
    op.drop_column("teams", "responsavel")
    op.drop_column("teams", "razao_social")
    op.drop_column("teams", "cnpj")
