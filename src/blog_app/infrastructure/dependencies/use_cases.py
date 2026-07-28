from typing import Annotated

from fastapi import Depends

from blog_app.infrastructure.dependencies.repositories import (
    RefreshTokenRepDep,
    UserCacheRepDep,
    UserRepDep,
)
from blog_app.infrastructure.dependencies.services.jwt_service import JWTServiceDep
from blog_app.infrastructure.dependencies.services.passwords import (
    PasswordComplexityValidatorDep,
    PasswordHasherDep,
)
from blog_app.use_cases.auth import (
    LoginAndIssueTokensUseCase,
    RegisterAndIssueTokensUseCase,
    ResolveCurrentUserUseCase,
)
from blog_app.use_cases.cache import InvalidateUserCacheUseCase
from blog_app.use_cases.tokens import (
    GetCurrentUserByAccessTokenUseCase,
    IssueTokenPairUseCase,
    RefreshTokenPairUseCase,
    RevokeRefreshTokenUseCase,
)
from blog_app.use_cases.users import (
    BaseUserUseCase,
    CreateUserUseCase,
    LoginUserUseCase,
)


def get_create_user_use_case(
    repo: UserRepDep,
    password_hasher: PasswordHasherDep,
    passwords_complexity_validator: PasswordComplexityValidatorDep,
) -> BaseUserUseCase:
    return CreateUserUseCase(
        repo=repo,
        password_complexity_validator=passwords_complexity_validator,
        password_hasher=password_hasher,
    )


CreateUserUseCaseDep = Annotated[
    CreateUserUseCase,
    Depends(get_create_user_use_case),
]


def get_login_user_use_case(
    repo: UserRepDep, password_hasher: PasswordHasherDep
) -> LoginUserUseCase:
    return LoginUserUseCase(
        repo=repo,
        password_hasher=password_hasher,
    )


LoginUserUseCaseDep = Annotated[
    LoginUserUseCase,
    Depends(get_login_user_use_case),
]


def get_issue_token_pair_use_case(
    token_service: JWTServiceDep,
    refresh_token_repo: RefreshTokenRepDep,
) -> IssueTokenPairUseCase:
    return IssueTokenPairUseCase(
        token_service=token_service,
        refresh_token_repo=refresh_token_repo,
    )


IssueTokenPairUseCaseDep = Annotated[
    IssueTokenPairUseCase,
    Depends(get_issue_token_pair_use_case),
]


def get_refresh_token_pair_use_case(
    token_service: JWTServiceDep,
    repo: UserRepDep,
    refresh_token_repo: RefreshTokenRepDep,
) -> RefreshTokenPairUseCase:
    return RefreshTokenPairUseCase(
        token_service=token_service,
        user_repo=repo,
        refresh_token_repo=refresh_token_repo,
    )


RefreshTokenPairUseCaseDep = Annotated[
    RefreshTokenPairUseCase,
    Depends(get_refresh_token_pair_use_case),
]


def get_revoke_refresh_token_use_case(
    token_service: JWTServiceDep,
    refresh_token_repo: RefreshTokenRepDep,
) -> RevokeRefreshTokenUseCase:
    return RevokeRefreshTokenUseCase(
        token_service=token_service,
        refresh_token_repo=refresh_token_repo,
    )


RevokeRefreshTokenUseCaseDep = Annotated[
    RevokeRefreshTokenUseCase,
    Depends(get_revoke_refresh_token_use_case),
]


def get_current_user_by_access_token_use_case(
    token_service: JWTServiceDep,
    repo: UserRepDep,
) -> GetCurrentUserByAccessTokenUseCase:
    return GetCurrentUserByAccessTokenUseCase(
        token_service=token_service,
        user_repo=repo,
    )


GetCurrentUserByAccessTokenUseCaseDep = Annotated[
    GetCurrentUserByAccessTokenUseCase,
    Depends(get_current_user_by_access_token_use_case),
]


def get_register_and_issue_tokens_use_case(
    create_user_use_case: CreateUserUseCaseDep,
    issue_token_pair_use_case: IssueTokenPairUseCaseDep,
) -> RegisterAndIssueTokensUseCase:
    return RegisterAndIssueTokensUseCase(
        create_user_use_case=create_user_use_case,
        issue_token_pair_use_case=issue_token_pair_use_case,
    )


RegisterAndIssueTokensUseCaseDep = Annotated[
    RegisterAndIssueTokensUseCase,
    Depends(get_register_and_issue_tokens_use_case),
]


def get_login_and_issue_tokens_use_case(
    login_user_use_case: LoginUserUseCaseDep,
    issue_token_pair_use_case: IssueTokenPairUseCaseDep,
) -> LoginAndIssueTokensUseCase:
    return LoginAndIssueTokensUseCase(
        login_user_use_case=login_user_use_case,
        issue_token_pair_use_case=issue_token_pair_use_case,
    )


LoginAndIssueTokensUseCaseDep = Annotated[
    LoginAndIssueTokensUseCase,
    Depends(get_login_and_issue_tokens_use_case),
]


def get_resolve_current_user_use_case(
    repo: UserRepDep,
    user_cache_repo: UserCacheRepDep,
) -> ResolveCurrentUserUseCase:
    return ResolveCurrentUserUseCase(
        user_repo=repo,
        user_cache_repo=user_cache_repo,
    )


ResolveCurrentUserUseCaseDep = Annotated[
    ResolveCurrentUserUseCase,
    Depends(get_resolve_current_user_use_case),
]


def get_invalidate_user_cache_use_case(
    user_cache_repo: UserCacheRepDep,
) -> InvalidateUserCacheUseCase:
    return InvalidateUserCacheUseCase(user_cache_repo=user_cache_repo)


InvalidateUserCacheUseCaseDep = Annotated[
    InvalidateUserCacheUseCase,
    Depends(get_invalidate_user_cache_use_case),
]
