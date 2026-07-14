from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class CreateUserCommand:
    username: str
    email: str
    password: str


@dataclass(frozen=True)
class LoginUserCommand:
    email: str
    password: str


@dataclass(frozen=True)
class ChangeUserUsernameCommand:
    id: UUID
    username: str


@dataclass(frozen=True)
class ChangeUserEmailCommand:
    id: UUID
    email: str
    password: str


@dataclass(frozen=True)
class ChangeUserPasswordCommand:
    id: UUID
    old_password: str | None
    new_password: str


@dataclass
class User:
    id: UUID | None
    username: str
    email: str
    hashed_password: str
    is_active: bool
    is_admin: bool
    registered_at: datetime | None
