"""0015 — add address column to merchants.

Stores the merchant's street address so it can be used as the default
pickup_address on new deliveries. Nullable — existing merchants keep working.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_merchant_address"
down_revision: str | None = "0014_delivery_package"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("merchants", sa.Column("address", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("merchants", "address")
