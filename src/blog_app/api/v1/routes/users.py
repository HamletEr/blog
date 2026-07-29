from uuid import UUID

from fastapi import APIRouter, Response
from starlette import status

from blog_app.api.auth_cookies import set_auth_cookies
from blog_app.api.v1.schemas.auth import AuthResponse
from blog_app.api.v1.schemas.users import (
    UserCreate,
    UserInfo,
    UserUpdateEmail,
    UserUpdatePassword,
    UserUpdateUsername,
)
from blog_app.core.config import settings
from blog_app.domain.entities.users import (
    ChangeUserEmailCommand,
    ChangeUserPasswordCommand,
    ChangeUserUsernameCommand,
    CreateUserCommand,
)
from blog_app.infrastructure.dependencies.use_cases import (
    ChangeEmailUseCaseDep,
    ChangePasswordUseCaseDep,
    ChangeUserActiveStatusUseCaseDep,
    ChangeUserAdminStatusUseCaseDep,
    ChangeUsernameUseCaseDep,
    RegisterAndIssueTokensUseCaseDep,
)

router: APIRouter = APIRouter(prefix="/users", tags=["users"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    response: Response,
    user_data: UserCreate,
    use_case: RegisterAndIssueTokensUseCaseDep,
) -> AuthResponse:
    command = CreateUserCommand(**user_data.model_dump())
    auth_result = await use_case.execute(command)
    set_auth_cookies(
        response,
        auth_result.tokens,
        access_max_age=settings.jwt_access_ttl_minutes * 60,
        refresh_max_age=settings.jwt_refresh_ttl_minutes * 60,
        secure=settings.app_env == "production",
    )
    return AuthResponse(user=UserInfo.model_validate(auth_result.user))


@router.patch("/{user_id}/username", status_code=status.HTTP_200_OK)
async def update_user_username(
    user_id: UUID, user_data: UserUpdateUsername, use_case: ChangeUsernameUseCaseDep
) -> UserInfo:
    command = ChangeUserUsernameCommand(
        id=user_id,
        username=user_data.username,
    )
    user_domain = await use_case.execute(command)
    return UserInfo.model_validate(user_domain)


@router.patch("/{user_id}/email", status_code=status.HTTP_200_OK)
async def update_user_email(
    user_id: UUID, user_data: UserUpdateEmail, use_case: ChangeEmailUseCaseDep
) -> UserInfo:
    command = ChangeUserEmailCommand(
        id=user_id,
        email=user_data.email,
        password=user_data.password,
    )
    user_domain = await use_case.execute(command)
    return UserInfo.model_validate(user_domain)


@router.patch("/{user_id}/password", status_code=status.HTTP_200_OK)
async def update_user_password(
    user_id: UUID, user_data: UserUpdatePassword, use_case: ChangePasswordUseCaseDep
) -> UserInfo:
    command = ChangeUserPasswordCommand(
        id=user_id,
        old_password=user_data.old_password,
        new_password=user_data.new_password,
    )
    user_domain = await use_case.execute(command)
    return UserInfo.model_validate(user_domain)


@router.patch("/{user_id}/status-active", status_code=status.HTTP_200_OK)
async def update_user_status_active(
    user_id: UUID, use_case: ChangeUserActiveStatusUseCaseDep
) -> UserInfo:
    user_domain = await use_case.execute(user_id)
    return UserInfo.model_validate(user_domain)


@router.patch("/{user_id}/status-admin", status_code=status.HTTP_200_OK)
async def update_user_status_admin(
    user_id: UUID, use_case: ChangeUserAdminStatusUseCaseDep
) -> UserInfo:
    user_domain = await use_case.execute(user_id)
    return UserInfo.model_validate(user_domain)
