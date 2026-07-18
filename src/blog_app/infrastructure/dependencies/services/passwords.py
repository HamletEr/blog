from typing import Annotated

from fastapi import Depends

from blog_app.domain.services.passwords import (
    PasswordComplexityValidator,
    PasswordHasher,
)
from blog_app.infrastructure.services.passwords import (
    Argon2PasswordHasher,
    PWComplexityValidator,
)


def get_password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()


PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]


def get_password_complexity_validator() -> PasswordComplexityValidator:
    return PWComplexityValidator()


PasswordComplexityValidatorDep = Annotated[
    PasswordComplexityValidator,
    Depends(get_password_complexity_validator),
]
