"""Drop polygon column from neighborhoods_catalog.

Polygon support was removed from the product — neighborhoods are now
identified by name only (is_informal flag still supported).
"""

from alembic import op

revision = "0029_drop_neighborhood_polygon"
down_revision = "0028_delivery_image_key"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("neighborhoods_catalog", "polygon")


def downgrade() -> None:
    # Restoring a SPATIAL column requires raw SQL (Alembic has no native type).
    op.execute(
        "ALTER TABLE neighborhoods_catalog "
        "ADD COLUMN polygon GEOMETRY NULL SRID 4326"
    )
