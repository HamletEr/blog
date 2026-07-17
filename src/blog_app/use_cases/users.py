from uuid import UUID

from blog_app.domain.entities.users import (
    ChangeUserEmailCommand,
    ChangeUserPasswordCommand,
    ChangeUserUsernameCommand,
    CreateUserCommand,
    LoginUserCommand,
    User,
)
from blog_app.domain.exceptions.users import (
    AuthenticationRequired,
    EmailAlreadyExists,
    IncorrectPassword,
    PermissionDenied,
    TooEasyPassword,
    UserAlreadyExists,
    UserNotFound,
)
from blog_app.domain.repositories.users import UserRepository
from blog_app.domain.services.passwords import (
    PasswordComplexityValidator,
    PasswordHasher,
)


def get_authenticated_user(user: User | None) -> User:
    if user:
        return user
    raise AuthenticationRequired()


def check_user_can_modify_user(
    current_user: User | None, modified_user_id: UUID | None
) -> None:
    user = get_authenticated_user(current_user)
    if not (user.is_admin or (user.id == modified_user_id)):
        raise PermissionDenied()


def check_password_complexity(
    password: str, validator: PasswordComplexityValidator
) -> None:
    errors = validator.get_violations(password)
    if errors:
        raise TooEasyPassword(" ".join(errors))


class BaseUserUseCase:
    def __init__(self, repo: UserRepository, current_user: User | None = None):
        self.repo = repo
        self.current_user = current_user

    async def get_user_by_id(self, user_id: UUID) -> User:
        user = await self.repo.get(user_id=user_id)
        if not user:
            raise UserNotFound()
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.repo.get(user_email=email)


class CreateUserUseCase(BaseUserUseCase):
    async def execute(
        self,
        user_data: CreateUserCommand,
        password_hasher: PasswordHasher,
        password_complexity_validator: PasswordComplexityValidator,
    ) -> User:
        user_with_email = await self.get_user_by_email(email=user_data.email)
        if user_with_email:
            raise UserAlreadyExists(user_data.email)
        check_password_complexity(user_data.password, password_complexity_validator)
        raw_user = User(
            id=None,
            username=user_data.username,
            email=user_data.email,
            hashed_password=await password_hasher.hash(user_data.password),
            is_active=True,
            is_admin=False,
            registered_at=None,
        )
        return await self.repo.create(raw_user)


class LoginUserUseCase(BaseUserUseCase):
    async def execute(
        self, user_data: LoginUserCommand, password_hasher: PasswordHasher
    ) -> User:
        user_with_email = await self.get_user_by_email(email=user_data.email)
        if not user_with_email or not await password_hasher.verify(
            user_data.password, user_with_email.hashed_password
        ):
            raise UserNotFound()
        if not user_with_email.is_active:
            raise PermissionDenied()
        return user_with_email


class ChangeUsernameUseCase(BaseUserUseCase):
    async def execute(self, user_data: ChangeUserUsernameCommand) -> User:
        check_user_can_modify_user(self.current_user, user_data.id)
        user = await self.get_user_by_id(user_data.id)
        user.username = user_data.username
        return await self.repo.update(user)


class ChangeEmailUseCase(BaseUserUseCase):
    async def execute(
        self, user_data: ChangeUserEmailCommand, password_hasher: PasswordHasher
    ) -> User:
        check_user_can_modify_user(self.current_user, user_data.id)
        self.current_user: User
        user = await self.get_user_by_id(user_data.id)
        if not self.current_user.is_admin and not await password_hasher.verify(
            user_data.password, user.hashed_password
        ):
            raise IncorrectPassword()
        user_with_new_email = await self.get_user_by_email(email=user_data.email)
        if user_with_new_email:
            raise EmailAlreadyExists(user_data.email)
        user.email = user_data.email
        return await self.repo.update(user)


class ChangePasswordUseCase(BaseUserUseCase):
    async def execute(
        self,
        user_data: ChangeUserPasswordCommand,
        password_hasher: PasswordHasher,
        password_complexity_validator: PasswordComplexityValidator,
    ) -> User:
        check_user_can_modify_user(self.current_user, user_data.id)
        self.current_user: User
        user = await self.get_user_by_id(user_data.id)
        if not self.current_user.is_admin and (
            not user_data.old_password
            or not await password_hasher.verify(
                user_data.old_password, user.hashed_password
            )
        ):
            raise IncorrectPassword()
        check_password_complexity(user_data.new_password, password_complexity_validator)
        user.hashed_password = await password_hasher.hash(user_data.new_password)
        return await self.repo.update(user)


class ChangeUserActiveStatusUseCase(BaseUserUseCase):
    async def execute(self, user_id: UUID) -> User:
        if not self.current_user or not self.current_user.is_admin:
            raise PermissionDenied()
        user = await self.get_user_by_id(user_id)
        user.is_active = not user.is_active
        return await self.repo.update(user)
