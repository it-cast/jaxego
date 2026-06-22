"""0016 — add courier_collection_method to deliveries.

Stores how the courier collected payment: 'in_hand' (cash/pix direto)
or 'pix_app' (cobra via PIX no app). Nullable — existing deliveries
keep working.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_courier_collection_method"
down_revision: str | None = "0015_merchant_address"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("deliveries", sa.Column("courier_collection_method", sa.String(16), nullable=True))


def downgrade() -> None:
    op.drop_column("deliveries", "courier_collection_method")
