from uuid import UUID

from blog_app.domain.entities.tokens import AuthResult
from blog_app.domain.entities.users import CreateUserCommand, LoginUserCommand, User
from blog_app.domain.exceptions.users import UserIdRequired, UserNotFound
from blog_app.domain.repositories.user_cache import UserCacheRepository
from blog_app.domain.repositories.users import UserRepository
from blog_app.use_cases.tokens import IssueTokenPairUseCase
from blog_app.use_cases.users import CreateUserUseCase, LoginUserUseCase


def get_existing_user_id(user_id: UUID | None) -> UUID:
    if user_id is None:
        raise UserIdRequired()
    return user_id


class RegisterAndIssueTokensUseCase:
    def __init__(
        self,
        create_user_use_case: CreateUserUseCase,
        issue_token_pair_use_case: IssueTokenPairUseCase,
    ) -> None:
        self.create_user_use_case = create_user_use_case
        self.issue_token_pair_use_case = issue_token_pair_use_case

    async def execute(self, user_data: CreateUserCommand) -> AuthResult:
        user = await self.create_user_use_case.execute(user_data)
        tokens = await self.issue_token_pair_use_case.execute(
            get_existing_user_id(user.id)
        )
        return AuthResult(user=user, tokens=tokens)


class LoginAndIssueTokensUseCase:
    def __init__(
        self,
        login_user_use_case: LoginUserUseCase,
        issue_token_pair_use_case: IssueTokenPairUseCase,
    ) -> None:
        self.login_user_use_case = login_user_use_case
        self.issue_token_pair_use_case = issue_token_pair_use_case

    async def execute(self, user_data: LoginUserCommand) -> AuthResult:
        user = await self.login_user_use_case.execute(user_data)
        tokens = await self.issue_token_pair_use_case.execute(
            get_existing_user_id(user.id)
        )
        return AuthResult(user=user, tokens=tokens)


class ResolveCurrentUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        user_cache_repo: UserCacheRepository,
    ) -> None:
        self.user_repo = user_repo
        self.user_cache_repo = user_cache_repo

    async def execute(self, user_id: UUID) -> User:
        user = await self.user_cache_repo.get(user_id)
        if user is not None:
            return user

        user = await self.user_repo.get(user_id=user_id)
        if user is None:
            raise UserNotFound()

        await self.user_cache_repo.save(user)
        return user


class InvalidateUserCacheUseCase:
    def __init__(self, user_cache_repo: UserCacheRepository) -> None:
        self.user_cache_repo = user_cache_repo

    async def execute(self, user_id: UUID) -> None:
        await self.user_cache_repo.delete(user_id)
