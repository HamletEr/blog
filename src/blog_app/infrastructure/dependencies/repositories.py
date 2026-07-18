from typing import Annotated

from fastapi import Depends

from blog_app.domain.repositories.users import UserRepository
from blog_app.infrastructure.dependencies.database import DbSessionDep
from blog_app.infrastructure.repositories.users import PGUserRepository


def get_user_repository(session: DbSessionDep) -> UserRepository:
    return PGUserRepository(session)


UserRepDep = Annotated[UserRepository, Depends(get_user_repository)]
