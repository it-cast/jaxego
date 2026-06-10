"""Declarative Base + MetaData with canonical naming convention (utf8mb4 / UTC).

Constraint naming convention (mysql-schema-design): ix/uq/ck/fk/pk so Alembic
generates stable, predictable constraint names. Charset utf8mb4 and collation
utf8mb4_unicode_ci are the table defaults. Timestamps are stored as DATETIME(6)
in UTC; conversion happens only at the boundary (TD-010).
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """Project-wide declarative base.

    Domain tables (Phase 2+) inherit from this. No domain table is defined in
    this foundation phase (REQ-022).
    """

    metadata = metadata

    # Table defaults applied to every domain table: utf8mb4 + UTC-friendly.
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }
