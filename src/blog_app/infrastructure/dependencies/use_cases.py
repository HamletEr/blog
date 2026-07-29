from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from blog_app.infrastructure.dependencies.auth import (
    CurrentUserDep,
    OptionalCurrentUserDep,
)
from blog_app.infrastructure.dependencies.repositories import (
    ArticleRepoDep,
    CategoryRepDep,
    RefreshTokenRepDep,
    UserCacheRepDep,
    UserRepDep,
)
from blog_app.infrastructure.dependencies.services.jwt_service import JWTServiceDep
from blog_app.infrastructure.dependencies.services.notifications import (
    UserRegistrationNotifierDep,
)
from blog_app.infrastructure.dependencies.services.passwords import (
    PasswordComplexityValidatorDep,
    PasswordHasherDep,
)
from blog_app.use_cases.articles import (
    CreateArticle,
    DeleteArticle,
    GetArticleById,
    GetListArticles,
    UpdateArticle,
)
from blog_app.use_cases.auth import (
    LoginAndIssueTokensUseCase,
    RegisterAndIssueTokensUseCase,
    ResolveCurrentUserUseCase,
)
from blog_app.use_cases.cache import InvalidateUserCacheUseCase
from blog_app.use_cases.categories import (
    CreateCategoryUseCase,
    GetByIdCategoryUseCase,
    GetListCategoryUseCase,
)
from blog_app.use_cases.tokens import (
    GetCurrentUserByAccessTokenUseCase,
    IssueTokenPairUseCase,
    RefreshTokenPairUseCase,
    RevokeRefreshTokenUseCase,
)
from blog_app.use_cases.users import (
    BaseUserUseCase,
    ChangeEmailUseCase,
    ChangePasswordUseCase,
    ChangeUserActiveStatusUseCase,
    ChangeUserAdminStatusUseCase,
    ChangeUsernameUseCase,
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


def get_change_username_use_case(
    repo: UserRepDep,
    invalidate_user_cache_use_case: InvalidateUserCacheUseCaseDep,
    user: CurrentUserDep,
) -> ChangeUsernameUseCase:
    return ChangeUsernameUseCase(
        repo=repo,
        invalidate_user_cache_use_case=invalidate_user_cache_use_case,
        current_user=user,
    )


ChangeUsernameUseCaseDep = Annotated[
    ChangeUsernameUseCase,
    Depends(get_change_username_use_case),
]


def get_change_email_use_case(
    repo: UserRepDep,
    password_hasher: PasswordHasherDep,
    invalidate_user_cache_use_case: InvalidateUserCacheUseCaseDep,
    user: CurrentUserDep,
) -> ChangeEmailUseCase:
    return ChangeEmailUseCase(
        repo=repo,
        password_hasher=password_hasher,
        invalidate_user_cache_use_case=invalidate_user_cache_use_case,
        current_user=user,
    )


ChangeEmailUseCaseDep = Annotated[
    ChangeEmailUseCase,
    Depends(get_change_email_use_case),
]


def get_change_password_use_case(
    repo: UserRepDep,
    refresh_token_repo: RefreshTokenRepDep,
    password_hasher: PasswordHasherDep,
    passwords_complexity_validator: PasswordComplexityValidatorDep,
    invalidate_user_cache_use_case: InvalidateUserCacheUseCaseDep,
    user: CurrentUserDep,
) -> ChangePasswordUseCase:
    return ChangePasswordUseCase(
        repo=repo,
        refresh_token_repo=refresh_token_repo,
        password_hasher=password_hasher,
        password_complexity_validator=passwords_complexity_validator,
        invalidate_user_cache_use_case=invalidate_user_cache_use_case,
        current_user=user,
    )


ChangePasswordUseCaseDep = Annotated[
    ChangePasswordUseCase,
    Depends(get_change_password_use_case),
]


def get_change_user_active_status_use_case(
    repo: UserRepDep,
    invalidate_user_cache_use_case: InvalidateUserCacheUseCaseDep,
    user: CurrentUserDep,
) -> ChangeUserActiveStatusUseCase:
    return ChangeUserActiveStatusUseCase(
        repo=repo,
        invalidate_user_cache_use_case=invalidate_user_cache_use_case,
        current_user=user,
    )


ChangeUserActiveStatusUseCaseDep = Annotated[
    ChangeUserActiveStatusUseCase,
    Depends(get_change_user_active_status_use_case),
]


def get_change_user_admin_status_use_case(
    repo: UserRepDep,
    invalidate_user_cache_use_case: InvalidateUserCacheUseCaseDep,
    user: CurrentUserDep,
) -> ChangeUserAdminStatusUseCase:
    return ChangeUserAdminStatusUseCase(
        repo=repo,
        invalidate_user_cache_use_case=invalidate_user_cache_use_case,
        current_user=user,
    )


ChangeUserAdminStatusUseCaseDep = Annotated[
    ChangeUserAdminStatusUseCase,
    Depends(get_change_user_admin_status_use_case),
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
    user_registration_notifier: UserRegistrationNotifierDep,
) -> RegisterAndIssueTokensUseCase:
    return RegisterAndIssueTokensUseCase(
        create_user_use_case=create_user_use_case,
        issue_token_pair_use_case=issue_token_pair_use_case,
        user_registration_notifier=user_registration_notifier,
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


def get_create_category_use_case(
    repo: CategoryRepDep, user: CurrentUserDep
) -> CreateCategoryUseCase:
    return CreateCategoryUseCase(repo=repo, user=user)


CreateCategoryUseCaseDep = Annotated[
    CreateCategoryUseCase, Depends(get_create_category_use_case)
]


def get_list_categories_use_case(
    repo: CategoryRepDep, user: OptionalCurrentUserDep
) -> GetListCategoryUseCase:
    return GetListCategoryUseCase(repo=repo, user=user)


GetListCategoryUseCaseDep = Annotated[
    GetListCategoryUseCase, Depends(get_list_categories_use_case)
]


def get_by_id_category_use_case(
    repo: CategoryRepDep, user: OptionalCurrentUserDep
) -> GetByIdCategoryUseCase:
    return GetByIdCategoryUseCase(repo=repo, user=user)


GetCategoryByIdUseCaseDep = Annotated[
    GetByIdCategoryUseCase, Depends(get_by_id_category_use_case)
]


def get_article_by_id_use_case(
    repo: ArticleRepoDep,
    user: OptionalCurrentUserDep,
) -> GetArticleById:
    return GetArticleById(repo=repo, user=user)


GetArticleByIdUseCaseDep = Annotated[
    GetArticleById, Depends(get_article_by_id_use_case)
]


def get_list_articles_use_case(
    repo: ArticleRepoDep, user: OptionalCurrentUserDep
) -> GetListArticles:
    return GetListArticles(repo=repo, user=user)


GetListArticlesUseCaseDep = Annotated[
    GetListArticles, Depends(get_list_articles_use_case)
]


def get_create_article_use_case(
    repo: ArticleRepoDep, user: CurrentUserDep
) -> CreateArticle:
    return CreateArticle(repo=repo, user=user)


CreateArticleUseCaseDep = Annotated[CreateArticle, Depends(get_create_article_use_case)]


def get_update_article_use_case(
    repo: ArticleRepoDep, user: CurrentUserDep
) -> UpdateArticle:
    return UpdateArticle(repo=repo, user=user)


UpdateArticleUseCaseDep = Annotated[UpdateArticle, Depends(get_update_article_use_case)]


def get_delete_article_use_case(
    repo: ArticleRepoDep, user: CurrentUserDep
) -> DeleteArticle:
    return DeleteArticle(repo=repo, user=user)


DeleteArticleUseCaseDep = Annotated[DeleteArticle, Depends(get_delete_article_use_case)]
