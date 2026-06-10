"""area operable: neighborhoods_catalog + courier coverage/pricing + couriers online (Phase 6)

Adds the Phase 6 "área operável" schema (REQ-002/003/016/017/018), reusing the
Phase 4/5 conventions: utf8mb4 tables, the inherited naming convention, FKs
RESTRICT (DRV-002), DATETIME(6) on MySQL, BIGINT ids, `Numeric` for money.

Three new AREA-SCOPED tables + two columns on `couriers`:

- `neighborhoods_catalog` — the per-area catalog the admin curates (D-01/D-02).
  A neighborhood is valid by NAME alone; the `polygon` is OPTIONAL (M1). The
  spatial column is added via RAW DDL only on MySQL (`POLYGON NULL SRID 4326`)
  so the SQLite test schema (Base.metadata.create_all) is never asked to model a
  native geometry type (Pitfall 3). All spatial read/write is via `func.ST_*`
  (Plan 02), never the ORM (LOW-1: no GeoAlchemy2).

  NO SPATIAL INDEX on `polygon`: SPATIAL indexes require NOT NULL, but the column
  is NULLABLE (optional M1) — Pitfall 1 / LOW-4. Pádua is small (full scan is
  cheap); tracked as TD-017 (post_launch_quarter): reavaliar >100 bairros/área
  com polígono.

- `courier_coverage_areas` — include/exclude rows per courier (RN-003 — coverage
  valid for BOTH pickup AND dropoff). UNIQUE (courier_id, neighborhood_id).

- `courier_pricing_tables` — pricing rows by neighborhood OR by km (A3), with a
  return % (RN-015). The platform NEVER fixes the price — it only imposes a floor
  (validated in the service, Plan 03). `price`/`return_pct` are `Numeric`.

- `couriers.is_online` (Boolean) + `couriers.max_concurrent` (Integer). `busy` is
  DERIVED from the load — NOT a column (D-06).

All datetime columns are DATETIME(6) UTC (TD-010).

Revision ID: 0005_area_operable
Revises: 0004_couriers_kyc
Create Date: 2026-06-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "0005_area_operable"
down_revision: str | None = "0004_couriers_kyc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE_KW = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}


def _dt() -> sa.types.TypeEngine:
    """DATETIME(6) on MySQL, plain DateTime elsewhere (SQLite dev)."""
    return sa.DateTime(timezone=True).with_variant(mysql.DATETIME(fsp=6), "mysql")


def upgrade() -> None:
    bind = op.get_bind()
    is_mysql = bind.dialect.name == "mysql"

    # --- neighborhoods_catalog (AREA-SCOPED — area_id NOT NULL FK to areas) ---
    op.create_table(
        "neighborhoods_catalog",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_informal", sa.Boolean(), nullable=False),
        # Soft-archive: removal with active deliveries is blocked → archive (Plan 02).
        sa.Column("archived_at", _dt(), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_neighborhoods_catalog")),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            name=op.f("fk_neighborhoods_catalog_area_id_areas"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        **_TABLE_KW,
    )
    op.create_index(op.f("ix_neighborhoods_catalog_area_id"), "neighborhoods_catalog", ["area_id"])
    # Catalog lookup by (area, name) — single-query list, no N+1.
    op.create_index(
        "ix_neighborhoods_catalog_area_id_name",
        "neighborhoods_catalog",
        ["area_id", "name"],
    )
    # Spatial column: MySQL-only RAW DDL (Alembic does not model native geometry).
    # POLYGON NULL SRID 4326 — manipulated only via func.ST_* (Plan 02). NO SPATIAL
    # INDEX: a SPATIAL index requires NOT NULL, but polygon is NULLABLE (Pitfall 1 /
    # LOW-4) → full scan in the Pádua pilot; TD-017 (post_launch_quarter).
    if is_mysql:
        op.execute("ALTER TABLE neighborhoods_catalog ADD COLUMN polygon POLYGON NULL SRID 4326")

    # --- courier_coverage_areas (AREA-SCOPED — include/exclude per courier) ---
    op.create_table(
        "courier_coverage_areas",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        sa.Column("neighborhood_id", sa.BigInteger(), nullable=False),
        # 'include' | 'exclude' (Pattern 3 — RN-003).
        sa.Column("kind", sa.String(length=8), nullable=False),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_courier_coverage_areas")),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            name=op.f("fk_courier_coverage_areas_area_id_areas"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["courier_id"],
            ["couriers.id"],
            name=op.f("fk_courier_coverage_areas_courier_id_couriers"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["neighborhood_id"],
            ["neighborhoods_catalog.id"],
            name=op.f("fk_courier_coverage_areas_neighborhood_id_neighborhoods_catalog"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        # One row per (courier, neighborhood) — include/exclude is exclusive.
        sa.UniqueConstraint(
            "courier_id",
            "neighborhood_id",
            name="uq_courier_coverage_areas_courier_id_neighborhood_id",
        ),
        **_TABLE_KW,
    )
    op.create_index(
        op.f("ix_courier_coverage_areas_area_id"), "courier_coverage_areas", ["area_id"]
    )
    op.create_index(
        op.f("ix_courier_coverage_areas_courier_id"),
        "courier_coverage_areas",
        ["courier_id"],
    )
    op.create_index(
        op.f("ix_courier_coverage_areas_neighborhood_id"),
        "courier_coverage_areas",
        ["neighborhood_id"],
    )

    # --- courier_pricing_tables (AREA-SCOPED — mode neighborhood|km, piso check) ---
    op.create_table(
        "courier_pricing_tables",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("courier_id", sa.BigInteger(), nullable=False),
        # 'neighborhood' | 'km' (A3).
        sa.Column("mode", sa.String(length=16), nullable=False),
        # Filled only in mode 'neighborhood'.
        sa.Column("neighborhood_id", sa.BigInteger(), nullable=True),
        # Filled only in mode 'km' (upper bound of the band).
        sa.Column("up_to_km", sa.Numeric(precision=6, scale=2), nullable=True),
        # R$ — Numeric (never Float). The courier sets it (>= area floor — RN-015).
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        # % return on the run (política de retorno) — 0..100.
        sa.Column("return_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("created_at", _dt(), nullable=False),
        sa.Column("updated_at", _dt(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_courier_pricing_tables")),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            name=op.f("fk_courier_pricing_tables_area_id_areas"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["courier_id"],
            ["couriers.id"],
            name=op.f("fk_courier_pricing_tables_courier_id_couriers"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["neighborhood_id"],
            ["neighborhoods_catalog.id"],
            name=op.f("fk_courier_pricing_tables_neighborhood_id_neighborhoods_catalog"),
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        **_TABLE_KW,
    )
    op.create_index(
        op.f("ix_courier_pricing_tables_area_id"), "courier_pricing_tables", ["area_id"]
    )
    # Per-courier pricing by mode — single-query read, no N+1.
    op.create_index(
        "ix_courier_pricing_tables_courier_id_mode",
        "courier_pricing_tables",
        ["courier_id", "mode"],
    )

    # --- couriers (ALTER): online state + max concurrent (busy is DERIVED) ---
    op.add_column(
        "couriers",
        sa.Column("is_online", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "couriers",
        sa.Column("max_concurrent", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )


def downgrade() -> None:
    op.drop_column("couriers", "max_concurrent")
    op.drop_column("couriers", "is_online")

    op.drop_index("ix_courier_pricing_tables_courier_id_mode", table_name="courier_pricing_tables")
    op.drop_index(op.f("ix_courier_pricing_tables_area_id"), table_name="courier_pricing_tables")
    op.drop_table("courier_pricing_tables")

    op.drop_index(
        op.f("ix_courier_coverage_areas_neighborhood_id"),
        table_name="courier_coverage_areas",
    )
    op.drop_index(op.f("ix_courier_coverage_areas_courier_id"), table_name="courier_coverage_areas")
    op.drop_index(op.f("ix_courier_coverage_areas_area_id"), table_name="courier_coverage_areas")
    op.drop_table("courier_coverage_areas")

    op.drop_index("ix_neighborhoods_catalog_area_id_name", table_name="neighborhoods_catalog")
    op.drop_index(op.f("ix_neighborhoods_catalog_area_id"), table_name="neighborhoods_catalog")
    op.drop_table("neighborhoods_catalog")
