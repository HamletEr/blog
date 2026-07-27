from abc import ABC, abstractmethod
from uuid import UUID

from blog_app.domain.entities.users import User


class UserCacheRepository(ABC):
    @abstractmethod
    async def get(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def save(self, user: User) -> None: ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> None: ...
