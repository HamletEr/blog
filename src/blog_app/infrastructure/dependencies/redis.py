from typing import Annotated, cast

from fastapi import Depends, Request
from redis.asyncio import Redis


def get_redis_client(request: Request) -> Redis:
    return cast(Redis, request.app.state.redis)


RedisDep = Annotated[Redis, Depends(get_redis_client)]
