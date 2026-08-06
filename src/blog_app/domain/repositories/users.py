from abc import ABC, abstractmethod
from uuid import UUID

from blog_app.domain.entities.users import User


class UserRepository(ABC):
    @abstractmethod
    async def get(
        self, user_id: UUID | None = None, user_email: str | None = None
    ) -> User | None: ...

    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def update(self, user: User) -> User: ...
