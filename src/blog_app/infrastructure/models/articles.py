from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import String, Text

from blog_app.core.database import Base
from blog_app.infrastructure.models.categories import CategoryArticleModel


class ArticleModel(Base):
    __tablename__ = "articles"
    id: Mapped[UUID] = mapped_column(primary_key=True, insert_default=uuid4)
    is_active: Mapped[bool] = mapped_column(default=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None]
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    category: Mapped[CategoryArticleModel | None] = relationship("CategoryArticleModel")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), insert_default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
