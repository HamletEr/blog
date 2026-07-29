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
from blog_app.domain.repositories.tokens import RefreshTokenRepository
from blog_app.domain.repositories.users import UserRepository
from blog_app.domain.services.passwords import (
    PasswordComplexityValidator,
    PasswordHasher,
)
from blog_app.use_cases.cache import InvalidateUserCacheUseCase


def get_authenticated_user(user: User | None) -> User:
    if user:
        return user
    raise AuthenticationRequired()


def require_admin(user: User) -> None:
    if not user.is_admin:
        raise PermissionDenied


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
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def get_user_by_id(self, user_id: UUID) -> User:
        user = await self.repo.get(user_id=user_id)
        if not user:
            raise UserNotFound()
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.repo.get(user_email=email)


class CreateUserUseCase(BaseUserUseCase):
    def __init__(
        self,
        repo: UserRepository,
        password_hasher: PasswordHasher,
        password_complexity_validator: PasswordComplexityValidator,
    ) -> None:
        super().__init__(repo)
        self.password_hasher = password_hasher
        self.password_complexity_validator = password_complexity_validator

    async def execute(self, user_data: CreateUserCommand) -> User:
        user_with_email = await self.get_user_by_email(email=user_data.email)
        if user_with_email:
            raise UserAlreadyExists(user_data.email)
        check_password_complexity(
            user_data.password, self.password_complexity_validator
        )
        raw_user = User(
            id=None,
            username=user_data.username,
            email=user_data.email,
            hashed_password=await self.password_hasher.hash(user_data.password),
            is_active=True,
            is_admin=False,
            registered_at=None,
        )
        return await self.repo.create(raw_user)


class LoginUserUseCase(BaseUserUseCase):
    def __init__(
        self,
        repo: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        super().__init__(repo)
        self.password_hasher = password_hasher

    async def execute(self, user_data: LoginUserCommand) -> User:
        user_with_email = await self.get_user_by_email(email=user_data.email)
        if not user_with_email or not await self.password_hasher.verify(
            user_data.password, user_with_email.hashed_password
        ):
            raise UserNotFound()
        if not user_with_email.is_active:
            raise PermissionDenied()
        return user_with_email


class ChangeUsernameUseCase(BaseUserUseCase):
    def __init__(
        self,
        repo: UserRepository,
        invalidate_user_cache_use_case: InvalidateUserCacheUseCase,
        current_user: User | None = None,
    ) -> None:
        super().__init__(repo)
        self.invalidate_user_cache_use_case = invalidate_user_cache_use_case
        self.current_user = current_user

    async def execute(self, user_data: ChangeUserUsernameCommand) -> User:
        check_user_can_modify_user(self.current_user, user_data.id)
        user = await self.get_user_by_id(user_data.id)
        user.username = user_data.username
        updated_user = await self.repo.update(user)
        await self.invalidate_user_cache_use_case.execute(user_data.id)
        return updated_user


class ChangeEmailUseCase(BaseUserUseCase):
    def __init__(
        self,
        repo: UserRepository,
        password_hasher: PasswordHasher,
        invalidate_user_cache_use_case: InvalidateUserCacheUseCase,
        current_user: User | None = None,
    ) -> None:
        super().__init__(repo)
        self.current_user = current_user
        self.password_hasher = password_hasher
        self.invalidate_user_cache_use_case = invalidate_user_cache_use_case

    async def execute(self, user_data: ChangeUserEmailCommand) -> User:
        check_user_can_modify_user(self.current_user, user_data.id)
        current_user = get_authenticated_user(self.current_user)
        user = await self.get_user_by_id(user_data.id)
        if not current_user.is_admin and (
            not user_data.password
            or not await self.password_hasher.verify(
                user_data.password, user.hashed_password
            )
        ):
            raise IncorrectPassword()
        user_with_new_email = await self.get_user_by_email(email=user_data.email)
        if user_with_new_email:
            raise EmailAlreadyExists(user_data.email)
        user.email = user_data.email
        updated_user = await self.repo.update(user)
        await self.invalidate_user_cache_use_case.execute(user_data.id)
        return updated_user


class ChangePasswordUseCase(BaseUserUseCase):
    def __init__(
        self,
        repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        password_hasher: PasswordHasher,
        password_complexity_validator: PasswordComplexityValidator,
        invalidate_user_cache_use_case: InvalidateUserCacheUseCase,
        current_user: User | None = None,
    ) -> None:
        super().__init__(repo)
        self.refresh_token_repo = refresh_token_repo
        self.current_user = current_user
        self.password_hasher = password_hasher
        self.password_complexity_validator = password_complexity_validator
        self.invalidate_user_cache_use_case = invalidate_user_cache_use_case

    async def execute(self, user_data: ChangeUserPasswordCommand) -> User:
        check_user_can_modify_user(self.current_user, user_data.id)
        current_user = get_authenticated_user(self.current_user)
        user = await self.get_user_by_id(user_data.id)
        if not current_user.is_admin and (
            not user_data.old_password
            or not await self.password_hasher.verify(
                user_data.old_password, user.hashed_password
            )
        ):
            raise IncorrectPassword()
        check_password_complexity(
            user_data.new_password, self.password_complexity_validator
        )
        user.hashed_password = await self.password_hasher.hash(user_data.new_password)
        updated_user = await self.repo.update(user)
        await self.refresh_token_repo.revoke_all_for_user(user_data.id)
        await self.invalidate_user_cache_use_case.execute(user_data.id)
        return updated_user


class ChangeUserActiveStatusUseCase(BaseUserUseCase):
    def __init__(
        self,
        repo: UserRepository,
        invalidate_user_cache_use_case: InvalidateUserCacheUseCase,
        current_user: User | None = None,
    ) -> None:
        super().__init__(repo)
        self.invalidate_user_cache_use_case = invalidate_user_cache_use_case
        self.current_user = current_user

    async def execute(self, user_id: UUID) -> User:
        if not self.current_user or not self.current_user.is_admin:
            raise PermissionDenied()
        user = await self.get_user_by_id(user_id)
        user.is_active = not user.is_active
        updated_user = await self.repo.update(user)
        await self.invalidate_user_cache_use_case.execute(user_id)
        return updated_user


class ChangeUserAdminStatusUseCase(BaseUserUseCase):
    def __init__(
        self,
        repo: UserRepository,
        invalidate_user_cache_use_case: InvalidateUserCacheUseCase,
        current_user: User | None = None,
    ) -> None:
        super().__init__(repo)
        self.invalidate_user_cache_use_case = invalidate_user_cache_use_case
        self.current_user = current_user

    async def execute(self, user_id: UUID) -> User:
        if not self.current_user or not self.current_user.is_admin:
            raise PermissionDenied()
        user = await self.get_user_by_id(user_id)
        user.is_admin = not user.is_admin
        updated_user = await self.repo.update(user)
        await self.invalidate_user_cache_use_case.execute(user_id)
        return updated_user
