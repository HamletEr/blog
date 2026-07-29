from uuid import uuid4

import pytest

from blog_app.domain.entities.users import User
from blog_app.domain.exceptions.users import UserIdRequired
from blog_app.infrastructure.repositories.user_cache import RedisUserCacheRepository


@pytest.mark.asyncio
async def test_save_and_get_user_from_cache(
    redis_client,
    redis_settings_stub,
    user_factory,
) -> None:
    repo = RedisUserCacheRepository(redis_client, redis_settings_stub)
    user = user_factory()

    await repo.save(user)
    cached_user = await repo.get(user.id)

    assert cached_user == user


@pytest.mark.asyncio
async def test_get_returns_none_for_missing_user_cache(
    redis_client,
    redis_settings_stub,
) -> None:
    repo = RedisUserCacheRepository(redis_client, redis_settings_stub)

    assert await repo.get(uuid4()) is None


@pytest.mark.asyncio
async def test_save_user_without_id_raises(
    redis_client,
    redis_settings_stub,
    user_factory,
) -> None:
    repo = RedisUserCacheRepository(redis_client, redis_settings_stub)
    user = User(
        id=None,
        username="alice",
        email="alice@example.com",
        hashed_password="hashed-password",
        is_active=True,
        is_admin=False,
        registered_at=None,
    )

    with pytest.raises(UserIdRequired):
        await repo.save(user)


@pytest.mark.asyncio
async def test_delete_removes_user_from_cache(
    redis_client,
    redis_settings_stub,
    user_factory,
) -> None:
    repo = RedisUserCacheRepository(redis_client, redis_settings_stub)
    user = user_factory()

    await repo.save(user)
    await repo.delete(user.id)

    assert await repo.get(user.id) is None
