from uuid import uuid4

import pytest

from blog_app.infrastructure.repositories.tokens import RedisRefreshTokenRepository


@pytest.mark.asyncio
async def test_save_and_exists_refresh_token(
    redis_client,
    redis_settings_stub,
) -> None:
    repo = RedisRefreshTokenRepository(redis_client, redis_settings_stub)
    token_id = uuid4()
    user_id = uuid4()

    await repo.save(token_id=token_id, user_id=user_id)

    assert await repo.exists(token_id=token_id, user_id=user_id) is True
    assert await repo.exists(token_id=token_id, user_id=uuid4()) is False


@pytest.mark.asyncio
async def test_revoke_refresh_token_removes_token_and_user_index(
    redis_client,
    redis_settings_stub,
) -> None:
    repo = RedisRefreshTokenRepository(redis_client, redis_settings_stub)
    token_id = uuid4()
    user_id = uuid4()

    await repo.save(token_id=token_id, user_id=user_id)
    await repo.revoke(token_id)

    assert await repo.exists(token_id=token_id, user_id=user_id) is False
    assert (
        await redis_client.smembers(
            RedisRefreshTokenRepository._user_refreshes_key(user_id)
        )
        == set()
    )


@pytest.mark.asyncio
async def test_revoke_missing_refresh_token_is_noop(
    redis_client,
    redis_settings_stub,
) -> None:
    repo = RedisRefreshTokenRepository(redis_client, redis_settings_stub)

    await repo.revoke(uuid4())

    assert await redis_client.dbsize() == 0


@pytest.mark.asyncio
async def test_revoke_all_for_user_removes_all_tokens(
    redis_client,
    redis_settings_stub,
) -> None:
    repo = RedisRefreshTokenRepository(redis_client, redis_settings_stub)
    user_id = uuid4()
    another_user_id = uuid4()
    token_ids = [uuid4(), uuid4()]
    another_token_id = uuid4()

    for token_id in token_ids:
        await repo.save(token_id=token_id, user_id=user_id)
    await repo.save(token_id=another_token_id, user_id=another_user_id)

    await repo.revoke_all_for_user(user_id)

    for token_id in token_ids:
        assert await repo.exists(token_id=token_id, user_id=user_id) is False
    assert await repo.exists(token_id=another_token_id, user_id=another_user_id) is True
    assert (
        await redis_client.exists(RedisRefreshTokenRepository._user_refreshes_key(user_id))
        == 0
    )
