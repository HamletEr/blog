from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from blog_app.core.database import Base


class CategoryModel(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
