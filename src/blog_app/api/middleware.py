from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from blog_app.api.auth_cookies import ACCESS_TOKEN_COOKIE_KEY
from blog_app.core.config import settings
from blog_app.core.database import AsyncSessionLocal
from blog_app.domain.entities.enums import TokenType
from blog_app.domain.exceptions.tokens import ExpiredToken, InvalidToken
from blog_app.domain.exceptions.users import PermissionDenied, UserNotFound
from blog_app.infrastructure.repositories.user_cache import RedisUserCacheRepository
from blog_app.infrastructure.repositories.users import PGUserRepository
from blog_app.infrastructure.services.jwt_service import JWTService
from blog_app.use_cases.auth import ResolveCurrentUserUseCase

PUBLIC_ROUTE_PREFIXES = ("/api/v1/health",)
PUBLIC_ROUTE_PAIRS = {
    ("POST", "/api/v1/users/"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/refresh"),
}


def is_public_route(request: Request) -> bool:
    if request.method == "OPTIONS":
        return True
    path = request.url.path
    if any(path.startswith(prefix) for prefix in PUBLIC_ROUTE_PREFIXES):
        return True
    return (request.method, path) in PUBLIC_ROUTE_PAIRS


def make_unauthorized_response() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": "Authentication required"},
    )


async def auth_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    if is_public_route(request):
        return await call_next(request)

    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE_KEY)
    if not access_token:
        return make_unauthorized_response()

    token_service = JWTService(settings)
    try:
        payload = token_service.decode_token(access_token, TokenType.ACCESS)
        user_id = UUID(payload["sub"])
    except (ExpiredToken, InvalidToken, ValueError):
        return make_unauthorized_response()

    async with AsyncSessionLocal() as session:
        user_repo = PGUserRepository(session)
        user_cache_repo = RedisUserCacheRepository(request.app.state.redis, settings)
        resolve_current_user_use_case = ResolveCurrentUserUseCase(
            user_repo=user_repo,
            user_cache_repo=user_cache_repo,
        )
        try:
            request.state.user = await resolve_current_user_use_case.execute(user_id)
        except (PermissionDenied, UserNotFound):
            return make_unauthorized_response()

    return await call_next(request)
