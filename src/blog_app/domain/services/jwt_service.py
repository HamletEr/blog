from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from blog_app.core.config import Settings
from blog_app.domain.entities.enums import TokenType


class TokenService(ABC):
    @abstractmethod
    def __init__(self, settings: Settings) -> None: ...

    @abstractmethod
    def create_token(
        self, user_id: UUID, token_type: TokenType, token_id: UUID | None = None
    ) -> str: ...

    @abstractmethod
    def decode_token(self, token: str, token_type: TokenType) -> dict[str, Any]: ...
