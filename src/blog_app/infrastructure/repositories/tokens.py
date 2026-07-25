from collections.abc import Awaitable
from datetime import timedelta
from typing import cast
from uuid import UUID

from redis.asyncio import Redis

from blog_app.core.config import Settings
from blog_app.domain.repositories.tokens import RefreshTokenRepository


class RedisRefreshTokenRepository(RefreshTokenRepository):
    # "_ =" in pipelines - is necessary that the ide does not swear as "Coroutine '...' is not awaited"
    # https://redis.io/docs/latest/develop/clients/redis-py/async/#pipelines-and-transactions

    def __init__(self, redis: Redis, settings: Settings) -> None:
        self._redis = redis
        self._refresh_ttl = timedelta(minutes=settings.jwt_refresh_ttl_minutes)

    @staticmethod
    def _refresh_key(token_id: UUID) -> str:
        return f"refresh:{token_id}"

    @staticmethod
    def _user_refreshes_key(user_id: UUID) -> str:
        return f"user_refreshes:{user_id}"

    async def save(self, token_id: UUID, user_id: UUID) -> None:
        refresh_key = self._refresh_key(token_id)
        user_refreshes_key = self._user_refreshes_key(user_id)

        async with self._redis.pipeline(transaction=True) as pipeline:
            _ = pipeline.set(refresh_key, str(user_id), ex=self._refresh_ttl)
            _ = pipeline.sadd(user_refreshes_key, str(token_id))
            _ = pipeline.expire(user_refreshes_key, self._refresh_ttl)
            await pipeline.execute()

    async def exists(self, token_id: UUID, user_id: UUID) -> bool:
        stored_user_id = await cast(
            Awaitable[str | None],
            self._redis.get(self._refresh_key(token_id)),
        )
        return stored_user_id == str(user_id)

    async def revoke(self, token_id: UUID) -> None:
        _ = refresh_key = self._refresh_key(token_id)
        _ = stored_user_id = await self._redis.get(refresh_key)
        if stored_user_id is None:
            return

        async with self._redis.pipeline(transaction=True) as pipeline:
            _ = pipeline.delete(refresh_key)
            _ = pipeline.srem(
                self._user_refreshes_key(UUID(stored_user_id)),
                str(token_id),
            )
            await pipeline.execute()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        user_refreshes_key = self._user_refreshes_key(user_id)
        token_ids = await cast(
            Awaitable[set[str]],
            self._redis.smembers(user_refreshes_key),
        )
        if not token_ids:
            return

        async with self._redis.pipeline(transaction=True) as pipeline:
            for token_id in token_ids:
                _ = pipeline.delete(self._refresh_key(UUID(token_id)))
            _ = pipeline.delete(user_refreshes_key)
            await pipeline.execute()
