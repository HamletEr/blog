from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import String, Text

from blog_app.core.database import Base


class ArticleModel(Base):
    __tablename__ = "articles"
    id: Mapped[UUID] = mapped_column(primary_key=True, default_factory=uuid4)
    is_active: Mapped[bool] = mapped_column(default=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    category_id: Mapped[int | None] = mapped_column(foreign_key="categories.id")
    image_url: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))


class CategoryArticleModel(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
