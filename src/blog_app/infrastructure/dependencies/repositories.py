from typing import Annotated

from fastapi import Depends

from blog_app.core.config import settings
from blog_app.domain.repositories.tokens import RefreshTokenRepository
from blog_app.domain.repositories.user_cache import UserCacheRepository
from blog_app.domain.repositories.users import UserRepository
from blog_app.infrastructure.dependencies.database import DbSessionDep
from blog_app.infrastructure.dependencies.redis import RedisDep
from blog_app.infrastructure.repositories.tokens import RedisRefreshTokenRepository
from blog_app.infrastructure.repositories.user_cache import RedisUserCacheRepository
from blog_app.infrastructure.repositories.users import PGUserRepository


def get_user_repository(session: DbSessionDep) -> UserRepository:
    return PGUserRepository(session)


def get_refresh_token_repository(redis: RedisDep) -> RefreshTokenRepository:
    return RedisRefreshTokenRepository(redis, settings)


def get_user_cache_repository(redis: RedisDep) -> UserCacheRepository:
    return RedisUserCacheRepository(redis, settings)


UserRepDep = Annotated[UserRepository, Depends(get_user_repository)]

RefreshTokenRepDep = Annotated[
    RefreshTokenRepository,
    Depends(get_refresh_token_repository),
]

UserCacheRepDep = Annotated[
    UserCacheRepository,
    Depends(get_user_cache_repository),
]
