from unittest.mock import AsyncMock, Mock, call
from uuid import UUID, uuid4

import pytest

from blog_app.domain.entities.enums import TokenType
from blog_app.domain.entities.tokens import TokenPair
from blog_app.domain.exceptions.tokens import InvalidToken
from blog_app.domain.exceptions.users import PermissionDenied, UserNotFound
from blog_app.use_cases.tokens import (
    GetCurrentUserByAccessTokenUseCase,
    IssueTokenPairUseCase,
    RefreshTokenPairUseCase,
    RevokeRefreshTokenUseCase,
)


@pytest.mark.asyncio
async def test_issue_token_pair_creates_tokens_and_saves_refresh_id() -> None:
    user_id = uuid4()
    token_service = Mock()
    token_service.create_token.side_effect = ["access-token", "refresh-token"]
    refresh_token_repo = AsyncMock()

    use_case = IssueTokenPairUseCase(
        token_service=token_service,
        refresh_token_repo=refresh_token_repo,
    )

    result = await use_case.execute(user_id)

    assert result == TokenPair(
        access_token="access-token",
        refresh_token="refresh-token",
    )
    assert token_service.create_token.call_args_list[0] == call(
        user_id=user_id,
        token_type=TokenType.ACCESS,
    )
    refresh_call = token_service.create_token.call_args_list[1]
    assert refresh_call.kwargs["user_id"] == user_id
    assert refresh_call.kwargs["token_type"] == TokenType.REFRESH
    assert isinstance(refresh_call.kwargs["token_id"], UUID)
    refresh_token_repo.save.assert_awaited_once_with(
        token_id=refresh_call.kwargs["token_id"],
        user_id=user_id,
    )


@pytest.mark.asyncio
async def test_refresh_token_pair_raises_for_revoked_refresh_token(user_factory) -> None:
    user = user_factory()
    token_id = uuid4()
    token_service = Mock()
    token_service.decode_token.return_value = {
        "sub": str(user.id),
        "jti": str(token_id),
    }
    user_repo = AsyncMock()
    refresh_token_repo = AsyncMock()
    refresh_token_repo.exists.return_value = False

    use_case = RefreshTokenPairUseCase(
        token_service=token_service,
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
    )

    with pytest.raises(InvalidToken):
        await use_case.execute("refresh-token")


@pytest.mark.asyncio
async def test_refresh_token_pair_raises_when_user_not_found(user_factory) -> None:
    user = user_factory()
    token_id = uuid4()
    token_service = Mock()
    token_service.decode_token.return_value = {
        "sub": str(user.id),
        "jti": str(token_id),
    }
    user_repo = AsyncMock()
    user_repo.get.return_value = None
    refresh_token_repo = AsyncMock()
    refresh_token_repo.exists.return_value = True

    use_case = RefreshTokenPairUseCase(
        token_service=token_service,
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
    )

    with pytest.raises(UserNotFound):
        await use_case.execute("refresh-token")


@pytest.mark.asyncio
async def test_refresh_token_pair_raises_for_inactive_user(user_factory) -> None:
    user = user_factory(is_active=False)
    token_id = uuid4()
    token_service = Mock()
    token_service.decode_token.return_value = {
        "sub": str(user.id),
        "jti": str(token_id),
    }
    user_repo = AsyncMock()
    user_repo.get.return_value = user
    refresh_token_repo = AsyncMock()
    refresh_token_repo.exists.return_value = True

    use_case = RefreshTokenPairUseCase(
        token_service=token_service,
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
    )

    with pytest.raises(PermissionDenied):
        await use_case.execute("refresh-token")


@pytest.mark.asyncio
async def test_refresh_token_pair_rotates_refresh_token(user_factory) -> None:
    user = user_factory()
    old_token_id = uuid4()
    token_service = Mock()
    token_service.decode_token.return_value = {
        "sub": str(user.id),
        "jti": str(old_token_id),
    }
    token_service.create_token.side_effect = ["new-access-token", "new-refresh-token"]
    user_repo = AsyncMock()
    user_repo.get.return_value = user
    refresh_token_repo = AsyncMock()
    refresh_token_repo.exists.return_value = True

    use_case = RefreshTokenPairUseCase(
        token_service=token_service,
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
    )

    result = await use_case.execute("refresh-token")

    assert result == TokenPair(
        access_token="new-access-token",
        refresh_token="new-refresh-token",
    )
    refresh_token_repo.revoke.assert_awaited_once_with(old_token_id)
    save_call = refresh_token_repo.save.await_args
    assert save_call.kwargs["user_id"] == user.id
    assert isinstance(save_call.kwargs["token_id"], UUID)
    assert save_call.kwargs["token_id"] != old_token_id


@pytest.mark.asyncio
async def test_revoke_refresh_token_decodes_and_revokes_jti() -> None:
    token_id = uuid4()
    token_service = Mock()
    token_service.decode_token.return_value = {"jti": str(token_id)}
    refresh_token_repo = AsyncMock()

    use_case = RevokeRefreshTokenUseCase(
        token_service=token_service,
        refresh_token_repo=refresh_token_repo,
    )

    await use_case.execute("refresh-token")

    token_service.decode_token.assert_called_once_with(
        "refresh-token",
        TokenType.REFRESH,
    )
    refresh_token_repo.revoke.assert_awaited_once_with(token_id)


@pytest.mark.asyncio
async def test_get_current_user_by_access_token_returns_active_user(user_factory) -> None:
    user = user_factory()
    token_service = Mock()
    token_service.decode_token.return_value = {"sub": str(user.id)}
    user_repo = AsyncMock()
    user_repo.get.return_value = user

    use_case = GetCurrentUserByAccessTokenUseCase(
        token_service=token_service,
        user_repo=user_repo,
    )

    result = await use_case.execute("access-token")

    assert result == user


@pytest.mark.asyncio
async def test_get_current_user_by_access_token_raises_for_missing_user() -> None:
    user_id = uuid4()
    token_service = Mock()
    token_service.decode_token.return_value = {"sub": str(user_id)}
    user_repo = AsyncMock()
    user_repo.get.return_value = None

    use_case = GetCurrentUserByAccessTokenUseCase(
        token_service=token_service,
        user_repo=user_repo,
    )

    with pytest.raises(UserNotFound):
        await use_case.execute("access-token")


@pytest.mark.asyncio
async def test_get_current_user_by_access_token_raises_for_inactive_user(
    user_factory,
) -> None:
    user = user_factory(is_active=False)
    token_service = Mock()
    token_service.decode_token.return_value = {"sub": str(user.id)}
    user_repo = AsyncMock()
    user_repo.get.return_value = user

    use_case = GetCurrentUserByAccessTokenUseCase(
        token_service=token_service,
        user_repo=user_repo,
    )

    with pytest.raises(UserNotFound):
        await use_case.execute("access-token")
