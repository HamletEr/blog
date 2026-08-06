from abc import ABC, abstractmethod
from uuid import UUID


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def save(self, token_id: UUID, user_id: UUID) -> None: ...

    @abstractmethod
    async def exists(self, token_id: UUID, user_id: UUID) -> bool: ...

    @abstractmethod
    async def revoke(self, token_id: UUID) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: UUID) -> None: ...
