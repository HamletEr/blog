from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Computed, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import String, Text

from blog_app.core.database import Base
from blog_app.infrastructure.models.categories import CategoryModel


class ArticleModel(Base):
    __tablename__ = "articles"
    __table_args__ = (
        Index(
            "ix_articles_search_vector",
            "search_vector",
            postgresql_using="gin",
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, insert_default=uuid4)
    is_active: Mapped[bool] = mapped_column(default=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('russian', coalesce(title, '')), 'A') || "
            "setweight(to_tsvector('russian', coalesce(content, '')), 'B')",
            persisted=True,
        ),
    )
    image_object_key: Mapped[str | None] = mapped_column(String(1024))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    category: Mapped[CategoryModel | None] = relationship("CategoryModel")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), insert_default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
