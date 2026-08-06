"""add article full text search

Revision ID: 6c2b1a9d4e3f
Revises: 8f1a2d4c9b7e
Create Date: 2026-08-01 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6c2b1a9d4e3f"
down_revision: str | Sequence[str] | None = "8f1a2d4c9b7e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE articles
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('russian', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('russian', coalesce(content, '')), 'B')
        ) STORED
        """
    )
    op.create_index(
        "ix_articles_search_vector",
        "articles",
        ["search_vector"],
        postgresql_using="gin",
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_articles_search_vector", table_name="articles")
    op.drop_column("articles", "search_vector")
