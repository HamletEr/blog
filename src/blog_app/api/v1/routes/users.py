from fastapi import APIRouter
from starlette import status

from blog_app.api.v1.schemas.users import UserCreate, UserInfo
from blog_app.domain.entities.users import CreateUserCommand
from blog_app.infrastructure.dependencies.use_cases import CreateUserUseCaseDep

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate, use_case: CreateUserUseCaseDep
) -> UserInfo:
    command = CreateUserCommand(**user_data.model_dump())
    user_domain = await use_case.execute(command)
    user_schema = UserInfo.model_validate(user_domain)
    # TODO:
    # - отправка email
    # - присвоение JWT
    # - обработка внутренних ошибок
    # - переадресация
    return user_schema
