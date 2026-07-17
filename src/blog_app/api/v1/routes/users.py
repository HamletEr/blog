from fastapi import APIRouter
from starlette import status

from blog_app.api.v1.schemas.users import UserCreate
from blog_app.domain.entities.users import CreateUserCommand

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate) -> None:
    user_create = CreateUserCommand(**user_data.model_dump())
    print(user_create)
