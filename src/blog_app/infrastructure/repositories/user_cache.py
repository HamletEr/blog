from datetime import UTC, datetime, timedelta
import json
from typing import Any, cast
from uuid import UUID

from redis.asyncio import Redis

from blog_app.core.config import Settings
from blog_app.domain.entities.users import User
from blog_app.domain.exceptions.users import UserIdRequired
from blog_app.domain.repositories.user_cache import UserCacheRepository


class RedisUserCacheRepository(UserCacheRepository):
    def __init__(self, redis: Redis, settings: Settings) -> None:
        self._redis = redis
        self._ttl = timedelta(minutes=settings.user_cache_ttl_minutes)

    @staticmethod
    def _user_key(user_id: UUID) -> str:
        return f"user_cache:{user_id}"

    @staticmethod
    def _serialize_user(user: User) -> str:
        payload = {
            "id": str(user.id) if user.id is not None else None,
            "username": user.username,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "registered_at": (
                user.registered_at.astimezone(UTC).isoformat()
                if user.registered_at is not None
                else None
            ),
        }
        return json.dumps(payload)

    @staticmethod
    def _deserialize_user(payload: str) -> User:
        data = cast(dict[str, Any], json.loads(payload))
        registered_at_raw = data["registered_at"]
        return User(
            id=UUID(data["id"]) if data["id"] is not None else None,
            username=str(data["username"]),
            email=str(data["email"]),
            hashed_password=str(data["hashed_password"]),
            is_active=bool(data["is_active"]),
            is_admin=bool(data["is_admin"]),
            registered_at=(
                datetime.fromisoformat(registered_at_raw)
                if registered_at_raw is not None
                else None
            ),
        )

    async def get(self, user_id: UUID) -> User | None:
        payload = await self._redis.get(self._user_key(user_id))
        if payload is None:
            return None
        return self._deserialize_user(payload)

    async def save(self, user: User) -> None:
        if user.id is None:
            raise UserIdRequired()
        await self._redis.set(
            self._user_key(user.id),
            self._serialize_user(user),
            ex=self._ttl,
        )

    async def delete(self, user_id: UUID) -> None:
        await self._redis.delete(self._user_key(user_id))
