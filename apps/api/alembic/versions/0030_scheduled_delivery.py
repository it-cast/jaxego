"""Add scheduled_at and inngest_event_id to deliveries.

Revision ID: 0030_scheduled_delivery
Revises: 0029_drop_neighborhood_polygon
Create Date: 2026-06-30

Enables scheduled deliveries (AGENDADA state): the store picks a future dispatch
time; Inngest fires a webhook at that time to transition AGENDADA → CRIADA and
kick off the cascade. `inngest_event_id` stores the Inngest event ID for
debugging / dashboard traceability.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0030_scheduled_delivery"
down_revision = "0029_drop_neighborhood_polygon"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("deliveries", sa.Column("scheduled_at", sa.DateTime(), nullable=True))
    op.add_column(
        "deliveries", sa.Column("inngest_event_id", sa.String(128), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("deliveries", "inngest_event_id")
    op.drop_column("deliveries", "scheduled_at")
