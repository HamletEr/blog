from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from blog_app.core.config import Settings
from blog_app.domain.entities.enums import TokenType
from blog_app.domain.exceptions.tokens import ExpiredToken, InvalidToken
from blog_app.domain.services.jwt_service import TokenService


class JWTService(TokenService):
    def __init__(self, settings: Settings):
        self._issuer = settings.app_name
        self._algorithm = settings.jwt_algorithm
        self._access_secret = settings.jwt_access_secret
        self._access_ttl = timedelta(minutes=settings.jwt_access_ttl_minutes)
        self._refresh_secret = settings.jwt_refresh_secret
        self._refresh_ttl = timedelta(minutes=settings.jwt_refresh_ttl_minutes)

    def create_token(
        self, user_id: UUID, token_type: TokenType, token_id: UUID | None = None
    ) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": token_type.value,
            "iat": now,
            "exp": now + self.__getattribute__(f"_{token_type.value}_ttl"),
            "iss": self._issuer,
        }
        if token_id is not None:
            payload["jti"] = str(token_id)

        return jwt.encode(
            payload=payload,
            key=self.__getattribute__(f"_{token_type.value}_secret"),
            algorithm=self._algorithm,
        )

    def decode_token(self, token: str, token_type: TokenType) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                key=self.__getattribute__(f"_{token_type.value}_secret"),
                algorithms=[self._algorithm],
                issuer=self._issuer,
            )
        except ExpiredSignatureError as exc:
            raise ExpiredToken() from exc
        except InvalidTokenError as exc:
            raise InvalidToken() from exc

        if payload.get("type") != token_type.value:
            raise InvalidToken()

        if token_type == TokenType.REFRESH and not payload.get("jti"):
            raise InvalidToken()

        return payload
