from fastapi import APIRouter
from starlette import status

from blog_app.api.v1.schemas.users import UserCreate
from blog_app.domain.entities.users import CreateUserCommand
from blog_app.infrastructure.dependencies.use_cases import CreateUserUseCaseDep

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, use_case: CreateUserUseCaseDep) -> None:
    command = CreateUserCommand(**user_data.model_dump())
    await use_case.execute(command)
