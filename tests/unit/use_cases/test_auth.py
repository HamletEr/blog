from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from blog_app.domain.entities.tokens import AuthResult, TokenPair
from blog_app.domain.entities.users import CreateUserCommand, LoginUserCommand
from blog_app.domain.exceptions.users import (
    PermissionDenied,
    UserIdRequired,
    UserNotFound,
)
from blog_app.use_cases.auth import (
    LoginAndIssueTokensUseCase,
    RegisterAndIssueTokensUseCase,
    ResolveCurrentUserUseCase,
    get_existing_user_id,
)


def test_get_existing_user_id_raises_when_none() -> None:
    with pytest.raises(UserIdRequired):
        get_existing_user_id(None)


@pytest.mark.asyncio
async def test_register_and_issue_tokens_returns_auth_result(user_factory) -> None:
    user = user_factory()
    tokens = TokenPair(access_token="access", refresh_token="refresh")
    create_user_use_case = AsyncMock()
    create_user_use_case.execute.return_value = user
    issue_token_pair_use_case = AsyncMock()
    issue_token_pair_use_case.execute.return_value = tokens

    use_case = RegisterAndIssueTokensUseCase(
        create_user_use_case=create_user_use_case,
        issue_token_pair_use_case=issue_token_pair_use_case,
    )

    command = CreateUserCommand(
        username="alice",
        email="alice@example.com",
        password="StrongPass123",
    )
    result = await use_case.execute(command)

    assert result == AuthResult(user=user, tokens=tokens)
    create_user_use_case.execute.assert_awaited_once_with(command)
    issue_token_pair_use_case.execute.assert_awaited_once_with(user.id)


@pytest.mark.asyncio
async def test_login_and_issue_tokens_returns_auth_result(user_factory) -> None:
    user = user_factory()
    tokens = TokenPair(access_token="access", refresh_token="refresh")
    login_user_use_case = AsyncMock()
    login_user_use_case.execute.return_value = user
    issue_token_pair_use_case = AsyncMock()
    issue_token_pair_use_case.execute.return_value = tokens

    use_case = LoginAndIssueTokensUseCase(
        login_user_use_case=login_user_use_case,
        issue_token_pair_use_case=issue_token_pair_use_case,
    )

    command = LoginUserCommand(email="alice@example.com", password="StrongPass123")
    result = await use_case.execute(command)

    assert result == AuthResult(user=user, tokens=tokens)
    login_user_use_case.execute.assert_awaited_once_with(command)
    issue_token_pair_use_case.execute.assert_awaited_once_with(user.id)


@pytest.mark.asyncio
async def test_resolve_current_user_returns_cached_user(user_factory) -> None:
    user = user_factory()
    user_repo = AsyncMock()
    user_cache_repo = AsyncMock()
    user_cache_repo.get.return_value = user

    use_case = ResolveCurrentUserUseCase(
        user_repo=user_repo,
        user_cache_repo=user_cache_repo,
    )

    result = await use_case.execute(user.id)

    assert result == user
    user_cache_repo.get.assert_awaited_once_with(user.id)
    user_repo.get.assert_not_called()
    user_cache_repo.save.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_current_user_rejects_inactive_cached_user(user_factory) -> None:
    user = user_factory(is_active=False)
    user_repo = AsyncMock()
    user_cache_repo = AsyncMock()
    user_cache_repo.get.return_value = user

    use_case = ResolveCurrentUserUseCase(
        user_repo=user_repo,
        user_cache_repo=user_cache_repo,
    )

    with pytest.raises(PermissionDenied):
        await use_case.execute(user.id)


@pytest.mark.asyncio
async def test_resolve_current_user_loads_from_repo_and_saves_cache(user_factory) -> None:
    user = user_factory()
    user_repo = AsyncMock()
    user_repo.get.return_value = user
    user_cache_repo = AsyncMock()
    user_cache_repo.get.return_value = None

    use_case = ResolveCurrentUserUseCase(
        user_repo=user_repo,
        user_cache_repo=user_cache_repo,
    )

    result = await use_case.execute(user.id)

    assert result == user
    user_repo.get.assert_awaited_once_with(user_id=user.id)
    user_cache_repo.save.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_resolve_current_user_raises_when_user_not_found() -> None:
    user_id = uuid4()
    user_repo = AsyncMock()
    user_repo.get.return_value = None
    user_cache_repo = AsyncMock()
    user_cache_repo.get.return_value = None

    use_case = ResolveCurrentUserUseCase(
        user_repo=user_repo,
        user_cache_repo=user_cache_repo,
    )

    with pytest.raises(UserNotFound):
        await use_case.execute(user_id)


@pytest.mark.asyncio
async def test_resolve_current_user_rejects_inactive_repo_user(user_factory) -> None:
    user = user_factory(is_active=False)
    user_repo = AsyncMock()
    user_repo.get.return_value = user
    user_cache_repo = AsyncMock()
    user_cache_repo.get.return_value = None

    use_case = ResolveCurrentUserUseCase(
        user_repo=user_repo,
        user_cache_repo=user_cache_repo,
    )

    with pytest.raises(PermissionDenied):
        await use_case.execute(user.id)

    user_cache_repo.save.assert_not_called()
