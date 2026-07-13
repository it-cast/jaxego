"""Remove a tabela global `users`: cada ator guarda as próprias credenciais.

- couriers/merchants/teams/area_admins ganham password_hash + lockout + is_active
- couriers ganha cpf; teams e area_admins ganham email; area_admins ganha name
- nova tabela platform_admins (ex users.platform_role='admin_plataforma', com TOTP)
- refresh_tokens: user_id -> actor_id + actor_type (tokens antigos são apagados)
- audit_log / delivery_state_transitions / deliveries / push_subscriptions ganham
  actor_type (linhas antigas ficam NULL — o id era users.id)
- drop merchant_users e users

Revision ID: 0045
Revises: 0044
Create Date: 2026-07-10
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0045"
down_revision = "0044"
branch_labels = None
depends_on = None


def _credentials_columns() -> list[sa.Column]:
    return [
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("first_failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    # ------------------------------------------------------------------ 1. couriers
    op.add_column("couriers", sa.Column("cpf", sa.String(11), nullable=True))
    for col in _credentials_columns():
        op.add_column("couriers", col)

    op.execute(
        """
        UPDATE couriers c JOIN users u ON u.id = c.user_id
        SET c.cpf = u.cpf, c.password_hash = u.password_hash,
            c.is_active = u.is_active
        """
    )

    op.drop_constraint("fk_couriers_user_id_users", "couriers", type_="foreignkey")
    op.drop_constraint("uq_couriers_area_id_user_id", "couriers", type_="unique")
    op.drop_index("ix_couriers_user_id", table_name="couriers")
    op.drop_column("couriers", "user_id")
    op.create_unique_constraint("uq_couriers_email", "couriers", ["email"])
    op.create_unique_constraint("uq_couriers_cpf", "couriers", ["cpf"])

    # ----------------------------------------------------------------- 2. merchants
    for col in _credentials_columns():
        op.add_column("merchants", col)

    op.execute(
        """
        UPDATE merchants m
        JOIN merchant_users mu ON mu.merchant_id = m.id
        JOIN users u ON u.id = mu.user_id
        SET m.password_hash = u.password_hash, m.is_active = u.is_active
        """
    )

    # --------------------------------------------------------------------- 3. teams
    op.add_column("teams", sa.Column("email", sa.String(255), nullable=True))
    for col in _credentials_columns():
        op.add_column("teams", col)

    op.execute(
        """
        UPDATE teams t JOIN users u ON u.id = t.responsavel_user_id
        SET t.email = u.email, t.password_hash = u.password_hash,
            t.is_active = u.is_active
        """
    )

    op.drop_constraint("fk_teams_responsavel_user_id", "teams", type_="foreignkey")
    op.drop_column("teams", "responsavel_user_id")
    op.create_unique_constraint("uq_teams_email", "teams", ["email"])

    # --------------------------------------------------------------- 4. area_admins
    op.add_column("area_admins", sa.Column("name", sa.String(160), nullable=False, server_default=""))
    op.add_column("area_admins", sa.Column("email", sa.String(255), nullable=True))
    for col in _credentials_columns():
        op.add_column("area_admins", col)

    op.execute(
        """
        UPDATE area_admins a JOIN users u ON u.id = a.user_id
        SET a.name = u.name, a.email = u.email,
            a.password_hash = u.password_hash, a.is_active = u.is_active
        """
    )

    op.drop_constraint("fk_area_admins_user_id_users", "area_admins", type_="foreignkey")
    op.drop_constraint("uq_area_admins_area_id_user_id", "area_admins", type_="unique")
    op.drop_index("ix_area_admins_user_id", table_name="area_admins")
    op.drop_column("area_admins", "user_id")
    op.create_unique_constraint("uq_area_admins_email", "area_admins", ["email"])

    # ----------------------------------------------------------- 5. platform_admins
    op.create_table(
        "platform_admins",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("first_failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("totp_secret", sa.String(64), nullable=True),
        sa.Column("totp_required", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("totp_enrolled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("totp_last_window", sa.BigInteger(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_platform_admins_email"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.execute(
        """
        INSERT INTO platform_admins
            (email, name, password_hash, is_active, failed_attempts,
             first_failed_at, locked_until, totp_secret, totp_required,
             totp_enrolled, totp_last_window, created_at, updated_at)
        SELECT email, name, password_hash, is_active, failed_attempts,
               first_failed_at, locked_until, totp_secret, totp_required,
               totp_enrolled, totp_last_window, created_at, updated_at
        FROM users WHERE platform_role = 'admin_plataforma'
        """
    )

    # ------------------------------------------------------------ 6. refresh_tokens
    # Sessões antigas apontavam para users.id — todas são invalidadas (re-login).
    op.execute("DELETE FROM refresh_tokens")
    op.add_column(
        "refresh_tokens",
        sa.Column("actor_type", sa.String(20), nullable=False, server_default="courier"),
    )
    op.alter_column(
        "refresh_tokens",
        "user_id",
        new_column_name="actor_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )

    # ------------------------------------------- 7. actor_type em tabelas de rastro
    op.add_column("audit_log", sa.Column("actor_type", sa.String(20), nullable=True))
    op.add_column(
        "delivery_state_transitions", sa.Column("actor_type", sa.String(20), nullable=True)
    )
    op.add_column("deliveries", sa.Column("cancel_actor_type", sa.String(20), nullable=True))
    op.add_column("push_subscriptions", sa.Column("actor_type", sa.String(20), nullable=True))

    # ------------------------------------------------------------------- 8. drops
    op.drop_table("merchant_users")
    op.drop_table("users")


def downgrade() -> None:
    raise NotImplementedError(
        "0045 é destrutiva (drop users/merchant_users) — restaure de backup."
    )
