from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from blog_app.core.database import Base


class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, insert_default=uuid4)
    username: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100))
    hashed_password: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    registered_at: Mapped[datetime] = mapped_column(
        insert_default=lambda: datetime.now(UTC)
    )
