from typing import Annotated, Any

from pydantic import (
    UUID4,
    AfterValidator,
    BaseModel,
    BeforeValidator,
    EmailStr,
    Field,
)


def strip_string(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


def normalize_email(value: EmailStr) -> EmailStr:
    return value.lower()


Password = Annotated[str, Field(min_length=8, max_length=100)]
Username = Annotated[
    str, Field(min_length=1, max_length=100), BeforeValidator(strip_string)
]
NormalizedEmail = Annotated[EmailStr, AfterValidator(normalize_email)]


class UserCreate(BaseModel):
    username: Username
    email: NormalizedEmail
    password: Password


class UserLogin(BaseModel):
    email: NormalizedEmail
    password: Password


class UserChangePassword(BaseModel):
    id: UUID4
    old_password: Password | None
    new_password: Password


class UserChangeUsername(BaseModel):
    id: UUID4
    username: Username


class UserChangeEmail(BaseModel):
    id: UUID4
    email: NormalizedEmail
    password: Password


class UserInfo(BaseModel):
    id: UUID4
    username: Username
    email: NormalizedEmail
    is_active: bool
    is_admin: bool
