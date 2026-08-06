from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from blog_app.api.exception_handlers import register_exception_handlers
from blog_app.api.middleware import auth_middleware
from blog_app.api.v1.router import main_router
from blog_app.core.config import settings
from blog_app.core.database import async_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    redis = Redis.from_url(settings.redis_dsn, decode_responses=True)
    app.state.redis = redis
    try:
        yield
    finally:
        await redis.aclose()
        await async_engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.app_name} ({settings.app_env})",
        version=settings.app_version,
        debug=settings.debug,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.middleware("http")(auth_middleware)
    register_exception_handlers(app)
    app.include_router(main_router)
    return app
