from fastapi import APIRouter, Response
from starlette import status

from blog_app.api.auth_cookies import set_auth_cookies
from blog_app.api.v1.schemas.auth import AuthResponse
from blog_app.api.v1.schemas.users import UserCreate, UserInfo
from blog_app.core.config import settings
from blog_app.domain.entities.users import CreateUserCommand
from blog_app.infrastructure.dependencies.use_cases import (
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
