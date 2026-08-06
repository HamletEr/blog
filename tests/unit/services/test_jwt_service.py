from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from blog_app.domain.entities.enums import TokenType
from blog_app.domain.exceptions.tokens import ExpiredToken, InvalidToken
from blog_app.infrastructure.services.jwt_service import JWTService


def test_create_and_decode_access_token(settings_stub) -> None:
    service = JWTService(settings_stub)
    user_id = uuid4()

    token = service.create_token(user_id=user_id, token_type=TokenType.ACCESS)
    payload = service.decode_token(token, TokenType.ACCESS)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == TokenType.ACCESS.value
    assert payload["iss"] == settings_stub.app_name
    assert "jti" not in payload


def test_create_and_decode_refresh_token_with_jti(settings_stub) -> None:
    service = JWTService(settings_stub)
    user_id = uuid4()
    token_id = uuid4()

    token = service.create_token(
        user_id=user_id,
        token_type=TokenType.REFRESH,
        token_id=token_id,
    )
    payload = service.decode_token(token, TokenType.REFRESH)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == TokenType.REFRESH.value
    assert payload["jti"] == str(token_id)


def test_decode_token_rejects_wrong_token_type(settings_stub) -> None:
    service = JWTService(settings_stub)
    token = service.create_token(user_id=uuid4(), token_type=TokenType.ACCESS)

    with pytest.raises(InvalidToken):
        service.decode_token(token, TokenType.REFRESH)


def test_decode_refresh_token_requires_jti(settings_stub) -> None:
    service = JWTService(settings_stub)
    now = datetime.now(UTC)
    token = jwt.encode(
        payload={
            "sub": str(uuid4()),
            "type": TokenType.REFRESH.value,
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "iss": settings_stub.app_name,
        },
        key=settings_stub.jwt_refresh_secret,
        algorithm=settings_stub.jwt_algorithm,
    )

    with pytest.raises(InvalidToken):
        service.decode_token(token, TokenType.REFRESH)


def test_decode_token_raises_expired_token(settings_stub) -> None:
    service = JWTService(settings_stub)
    now = datetime.now(UTC)
    token = jwt.encode(
        payload={
            "sub": str(uuid4()),
            "type": TokenType.ACCESS.value,
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=5),
            "iss": settings_stub.app_name,
        },
        key=settings_stub.jwt_access_secret,
        algorithm=settings_stub.jwt_algorithm,
    )

    with pytest.raises(ExpiredToken):
        service.decode_token(token, TokenType.ACCESS)
