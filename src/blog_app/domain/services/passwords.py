from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    @abstractmethod
    async def hash(self, password: str) -> str: ...

    @abstractmethod
    async def verify(self, password: str, hashed_password: str) -> bool: ...
