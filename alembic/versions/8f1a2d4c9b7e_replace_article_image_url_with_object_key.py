"""replace article image url with object key

Revision ID: 8f1a2d4c9b7e
Revises: 4093c7ff35bc
Create Date: 2026-07-31 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f1a2d4c9b7e"
down_revision: str | Sequence[str] | None = "4093c7ff35bc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("image_object_key", sa.String(length=1024), nullable=True),
    )
    op.drop_column("articles", "image_url")


def downgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("image_url", sa.String(), nullable=True),
    )
    op.drop_column("articles", "image_object_key")
