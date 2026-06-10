"""baseline (empty — no domain tables)

Establishes the migration chain and the naming/charset conventions. No domain
table is created in the foundation phase (REQ-022, D-04). Applies and reverts
cleanly so downstream phases can build on a known baseline.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-10

"""

from __future__ import annotations

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Intentionally empty: baseline carries no domain schema.
    pass


def downgrade() -> None:
    # Intentionally empty: nothing to revert in the baseline.
    pass
