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
