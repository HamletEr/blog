from typing import Annotated

from fastapi import Depends

from blog_app.core.config import settings
from blog_app.domain.repositories.articles import ArticleRepository
from blog_app.domain.repositories.categories import CategoryRepository
from blog_app.domain.repositories.tokens import RefreshTokenRepository
from blog_app.domain.repositories.user_cache import UserCacheRepository
from blog_app.domain.repositories.users import UserRepository
from blog_app.infrastructure.dependencies.database import DbSessionDep
from blog_app.infrastructure.dependencies.redis import RedisDep
from blog_app.infrastructure.repositories.articles import PGArticleRepository
from blog_app.infrastructure.repositories.categories import PGCategoryRepository
from blog_app.infrastructure.repositories.tokens import RedisRefreshTokenRepository
from blog_app.infrastructure.repositories.user_cache import RedisUserCacheRepository
from blog_app.infrastructure.repositories.users import PGUserRepository


def get_user_repository(session: DbSessionDep) -> UserRepository:
    return PGUserRepository(session)


UserRepDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_article_repository(session: DbSessionDep) -> ArticleRepository:
    return PGArticleRepository(session)


ArticleRepoDep = Annotated[ArticleRepository, Depends(get_article_repository)]


def get_category_repository(session: DbSessionDep) -> CategoryRepository:
    return PGCategoryRepository(session)


CategoryRepDep = Annotated[CategoryRepository, Depends(get_category_repository)]


def get_refresh_token_repository(redis: RedisDep) -> RefreshTokenRepository:
    return RedisRefreshTokenRepository(redis, settings)


RefreshTokenRepDep = Annotated[
    RefreshTokenRepository,
    Depends(get_refresh_token_repository),
]


def get_user_cache_repository(redis: RedisDep) -> UserCacheRepository:
    return RedisUserCacheRepository(redis, settings)


UserCacheRepDep = Annotated[
    UserCacheRepository,
    Depends(get_user_cache_repository),
]
