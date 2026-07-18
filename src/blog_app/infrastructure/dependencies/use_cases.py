from typing import Annotated

from fastapi import Depends

from blog_app.domain.entities.users import User
from blog_app.infrastructure.dependencies.repositories import UserRepDep
from blog_app.infrastructure.dependencies.services.passwords import (
    PasswordComplexityValidatorDep,
    PasswordHasherDep,
)
from blog_app.use_cases.users import BaseUserUseCase, CreateUserUseCase


def get_create_user_use_case(
    repo: UserRepDep,
    password_hasher: PasswordHasherDep,
    passwords_complexity_validator: PasswordComplexityValidatorDep,
    user: User | None = None,
) -> BaseUserUseCase:
    return CreateUserUseCase(
        repo=repo,
        current_user=user,
        password_complexity_validator=passwords_complexity_validator,
        password_hasher=password_hasher,
    )


CreateUserUseCaseDep = Annotated[
    CreateUserUseCase,
    Depends(get_create_user_use_case),
]
