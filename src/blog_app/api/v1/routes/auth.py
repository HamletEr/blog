from contextlib import suppress

from fastapi import APIRouter, HTTPException, Request, Response
from starlette import status

from blog_app.api.auth_cookies import (
    REFRESH_TOKEN_COOKIE_KEY,
    clear_auth_cookies,
    set_auth_cookies,
)
from blog_app.api.v1.schemas.auth import AuthResponse, MessageResponse
from blog_app.api.v1.schemas.users import UserInfo, UserLogin
from blog_app.core.config import settings
from blog_app.domain.entities.users import LoginUserCommand
from blog_app.domain.exceptions.tokens import ExpiredToken, InvalidToken
from blog_app.domain.exceptions.users import PermissionDenied, UserNotFound
from blog_app.infrastructure.dependencies.auth import CurrentUserDep
from blog_app.infrastructure.dependencies.use_cases import (
    LoginAndIssueTokensUseCaseDep,
    RefreshTokenPairUseCaseDep,
    RevokeRefreshTokenUseCaseDep,
)

router: APIRouter = APIRouter(prefix="/auth", tags=["auth"])


def use_secure_cookies() -> bool:
    return settings.app_env == "production"


def access_max_age_seconds() -> int:
    return settings.jwt_access_ttl_minutes * 60


def refresh_max_age_seconds() -> int:
    return settings.jwt_refresh_ttl_minutes * 60


@router.post("/login", response_model=AuthResponse)
async def login(
    response: Response,
    user_data: UserLogin,
    use_case: LoginAndIssueTokensUseCaseDep,
) -> AuthResponse:
    auth_result = await use_case.execute(LoginUserCommand(**user_data.model_dump()))
    set_auth_cookies(
        response,
        auth_result.tokens,
        access_max_age=access_max_age_seconds(),
        refresh_max_age=refresh_max_age_seconds(),
        secure=use_secure_cookies(),
    )
    return AuthResponse(user=UserInfo.model_validate(auth_result.user))


@router.post("/refresh", response_model=MessageResponse)
async def refresh_session(
    request: Request,
    response: Response,
    use_case: RefreshTokenPairUseCaseDep,
) -> MessageResponse:
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_KEY)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing",
        )

    try:
        token_pair = await use_case.execute(refresh_token)
    except (ExpiredToken, InvalidToken, PermissionDenied, UserNotFound) as exc:
        clear_auth_cookies(response, secure=use_secure_cookies())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc

    set_auth_cookies(
        response,
        token_pair,
        access_max_age=access_max_age_seconds(),
        refresh_max_age=refresh_max_age_seconds(),
        secure=use_secure_cookies(),
    )
    return MessageResponse(detail="Session refreshed")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    use_case: RevokeRefreshTokenUseCaseDep,
) -> Response:
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_KEY)
    if refresh_token:
        with suppress(ExpiredToken, InvalidToken):
            await use_case.execute(refresh_token)

    clear_auth_cookies(response, secure=use_secure_cookies())
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: CurrentUserDep) -> UserInfo:
    return UserInfo.model_validate(current_user)
