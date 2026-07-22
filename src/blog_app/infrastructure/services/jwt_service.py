from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from blog_app.core.config import Settings


class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenService:
    def __init__(self, settings: Settings):
        self._issuer = settings.app_name
        self._algorithm = settings.jwt_algorithm
        self._access_secret = settings.jwt_access_secret
        self._access_ttl = timedelta(minutes=settings.jwt_access_ttl_minutes)
        self._refresh_secret = settings.jwt_refresh_secret
        self._refresh_ttl = timedelta(minutes=settings.jwt_refresh_ttl_minutes)

    def create_token(self, user_id: UUID, token_type: TokenType) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            payload={
                "sub": str(user_id),
                "type": token_type.value,
                "iat": now,
                "exp": now + self.__getattribute__(f"_{token_type.value}_ttl"),
                "iss": self._issuer,
            },
            key=self.__getattribute__(f"_{token_type.value}_secret"),
            algorithm=self._algorithm,
        )

    def decode_token(self, token: str, token_type: TokenType) -> dict[str, Any]:
        payload = jwt.decode(
            token,
            key=self.__getattribute__(f"_{token_type.value}_secret"),
            algorithms=[self._algorithm],
            issuer=self._issuer,
        )
        if payload.get("type") != token_type.value:
            raise InvalidTokenError()
        return payload
