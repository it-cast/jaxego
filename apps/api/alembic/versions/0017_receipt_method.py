"""0017 — add receipt_method to deliveries.

Stores how the merchant wants the customer to pay for the order:
'dinheiro', 'maquina_loja', or 'aplicativo'. Nullable for existing rows.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_receipt_method"
down_revision: str | None = "0016_courier_collection_method"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("deliveries", sa.Column("receipt_method", sa.String(16), nullable=True))


def downgrade() -> None:
    op.drop_column("deliveries", "receipt_method")
