from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
import pytest_asyncio
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from blog_app.api.app import create_app
from blog_app.core.config import settings
from blog_app.domain.entities.users import User


@pytest.fixture
def settings_stub() -> SimpleNamespace:
    return SimpleNamespace(
        app_name="blog-app",
        jwt_algorithm="HS256",
        jwt_access_secret="access-secret-access-secret-1234",
        jwt_access_ttl_minutes=15,
        jwt_refresh_secret="refresh-secret-refresh-secret-1234",
        jwt_refresh_ttl_minutes=60,
    )


@pytest.fixture
def user_factory() -> Any:
    def make_user(**kwargs: Any) -> User:
        return User(
            id=kwargs.pop("id", uuid4()),
            username=kwargs.pop("username", "alice"),
            email=kwargs.pop("email", "alice@example.com"),
            hashed_password=kwargs.pop("hashed_password", "hashed-secret"),
            is_active=kwargs.pop("is_active", True),
            is_admin=kwargs.pop("is_admin", False),
            registered_at=kwargs.pop("registered_at", datetime.now(UTC)),
        )

    return make_user


@pytest.fixture
def redis_settings_stub() -> SimpleNamespace:
    return SimpleNamespace(
        jwt_refresh_ttl_minutes=60,
        user_cache_ttl_minutes=30,
    )


@pytest_asyncio.fixture
async def redis_client() -> Any:
    parsed = urlparse(settings.redis_dsn)
    test_redis_dsn = parsed._replace(path="/15").geturl()
    redis = Redis.from_url(test_redis_dsn, decode_responses=True)
    try:
        await redis.flushdb()
    except RedisConnectionError:
        await redis.aclose()
        pytest.skip("Redis is not available for integration tests")
    try:
        yield redis
    finally:
        await redis.flushdb()
        await redis.aclose()


@pytest.fixture
def app() -> Any:
    app = create_app()
    try:
        yield app
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def client(app) -> Any:
    with TestClient(app) as test_client:
        yield test_client
