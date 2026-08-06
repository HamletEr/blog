from unittest.mock import AsyncMock, Mock

import pytest

from blog_app.domain.entities.users import (
    ChangeUserEmailCommand,
    ChangeUserPasswordCommand,
    ChangeUserUsernameCommand,
    CreateUserCommand,
    LoginUserCommand,
)
from blog_app.domain.exceptions.users import (
    IncorrectPassword,
    PermissionDenied,
    TooEasyPassword,
    UserAlreadyExists,
    UserNotFound,
)
from blog_app.use_cases.users import (
    ChangeEmailUseCase,
    ChangePasswordUseCase,
    ChangeUserActiveStatusUseCase,
    ChangeUserAdminStatusUseCase,
    ChangeUsernameUseCase,
    CreateUserUseCase,
    LoginUserUseCase,
)


@pytest.mark.asyncio
async def test_create_user_creates_hashed_user(user_factory) -> None:
    repo = AsyncMock()
    repo.get.return_value = None
    created_user = user_factory()
    repo.create.return_value = created_user
    password_hasher = AsyncMock()
    password_hasher.hash.return_value = "hashed-password"
    password_complexity_validator = Mock()
    password_complexity_validator.get_violations.return_value = []

    use_case = CreateUserUseCase(
        repo=repo,
        password_hasher=password_hasher,
        password_complexity_validator=password_complexity_validator,
    )

    command = CreateUserCommand(
        username="alice",
        email="alice@example.com",
        password="StrongPass123",
    )
    result = await use_case.execute(command)

    assert result == created_user
    password_hasher.hash.assert_awaited_once_with(command.password)
    created_arg = repo.create.await_args.args[0]
    assert created_arg.id is None
    assert created_arg.username == command.username
    assert created_arg.email == command.email
    assert created_arg.hashed_password == "hashed-password"
    assert created_arg.is_active is True
    assert created_arg.is_admin is False


@pytest.mark.asyncio
async def test_create_user_raises_for_duplicate_email() -> None:
    repo = AsyncMock()
    repo.get.return_value = object()
    password_hasher = AsyncMock()
    password_complexity_validator = Mock()

    use_case = CreateUserUseCase(
        repo=repo,
        password_hasher=password_hasher,
        password_complexity_validator=password_complexity_validator,
    )

    with pytest.raises(UserAlreadyExists):
        await use_case.execute(
            CreateUserCommand(
                username="alice",
                email="alice@example.com",
                password="StrongPass123",
            )
        )


@pytest.mark.asyncio
async def test_create_user_raises_for_too_easy_password() -> None:
    repo = AsyncMock()
    repo.get.return_value = None
    password_hasher = AsyncMock()
    password_complexity_validator = Mock()
    password_complexity_validator.get_violations.return_value = ["too short"]

    use_case = CreateUserUseCase(
        repo=repo,
        password_hasher=password_hasher,
        password_complexity_validator=password_complexity_validator,
    )

    with pytest.raises(TooEasyPassword):
        await use_case.execute(
            CreateUserCommand(
                username="alice",
                email="alice@example.com",
                password="weak",
            )
        )

    repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_login_user_returns_user_for_correct_credentials(user_factory) -> None:
    user = user_factory()
    repo = AsyncMock()
    repo.get.return_value = user
    password_hasher = AsyncMock()
    password_hasher.verify.return_value = True

    use_case = LoginUserUseCase(repo=repo, password_hasher=password_hasher)

    result = await use_case.execute(
        LoginUserCommand(email=user.email, password="StrongPass123")
    )

    assert result == user


@pytest.mark.asyncio
async def test_login_user_raises_for_invalid_password(user_factory) -> None:
    user = user_factory()
    repo = AsyncMock()
    repo.get.return_value = user
    password_hasher = AsyncMock()
    password_hasher.verify.return_value = False

    use_case = LoginUserUseCase(repo=repo, password_hasher=password_hasher)

    with pytest.raises(UserNotFound):
        await use_case.execute(
            LoginUserCommand(email=user.email, password="wrong-password")
        )


@pytest.mark.asyncio
async def test_login_user_raises_for_inactive_user(user_factory) -> None:
    user = user_factory(is_active=False)
    repo = AsyncMock()
    repo.get.return_value = user
    password_hasher = AsyncMock()
    password_hasher.verify.return_value = True

    use_case = LoginUserUseCase(repo=repo, password_hasher=password_hasher)

    with pytest.raises(PermissionDenied):
        await use_case.execute(
            LoginUserCommand(email=user.email, password="StrongPass123")
        )


@pytest.mark.asyncio
async def test_change_username_updates_user_for_owner(user_factory) -> None:
    user = user_factory()
    repo = AsyncMock()
    repo.get.return_value = user
    updated_user = user_factory(id=user.id, username="new-name")
    repo.update.return_value = updated_user
    invalidate_user_cache_use_case = AsyncMock()

    use_case = ChangeUsernameUseCase(
        repo=repo,
        invalidate_user_cache_use_case=invalidate_user_cache_use_case,
        current_user=user,
    )

    result = await use_case.execute(
        ChangeUserUsernameCommand(id=user.id, username="new-name")
    )

    assert result == updated_user
    invalidate_user_cache_use_case.execute.assert_awaited_once_with(user.id)


@pytest.mark.asyncio
async def test_change_username_rejects_non_owner_non_admin(user_factory) -> None:
    current_user = user_factory()
    target_user = user_factory()
    repo = AsyncMock()
    invalidate_user_cache_use_case = AsyncMock()

    use_case = ChangeUsernameUseCase(
        repo=repo,
        invalidate_user_cache_use_case=invalidate_user_cache_use_case,
        current_user=current_user,
    )

    with pytest.raises(PermissionDenied):
        await use_case.execute(
            ChangeUserUsernameCommand(id=target_user.id, username="new-name")
        )


@pytest.mark.asyncio
async def test_change_email_requires_password_for_non_admin(user_factory) -> None:
    user = user_factory()
    repo = AsyncMock()
    repo.get.side_effect = [user, user]
    password_hasher = AsyncMock()
    password_hasher.verify.return_value = False
    invalidate_user_cache_use_case = AsyncMock()

    use_case = ChangeEmailUseCase(
        repo=repo,
        password_hasher=password_hasher,
        invalidate_user_cache_use_case=invalidate_user_cache_use_case,
        current_user=user,
    )

    with pytest.raises(IncorrectPassword):
        await use_case.execute(
            ChangeUserEmailCommand(
                id=user.id,
                email="new@example.com",
                password="wrong-password",
            )
        )


@pytest.mark.asyncio
async def test_change_email_allows_admin_without_password(user_factory) -> None:
    admin_user = user_factory(is_admin=True)
    target_user = user_factory()
    updated_user = user_factory(id=target_user.id, email="new@example.com")
    repo = AsyncMock()
    repo.get.side_effect = [target_user, None]
    repo.update.return_value = updated_user
    password_hasher = AsyncMock()
    invalidate_user_cache_use_case = AsyncMock()

    use_case = ChangeEmailUseCase(
        repo=repo,
        password_hasher=password_hasher,
        invalidate_user_cache_use_case=invalidate_user_cache_use_case,
        current_user=admin_user,
    )

    result = await use_case.execute(
        ChangeUserEmailCommand(
            id=target_user.id,
            email="new@example.com",
            password=None,
        )
    )

    assert result == updated_user
    password_hasher.verify.assert_not_called()
    invalidate_user_cache_use_case.execute.assert_awaited_once_with(target_user.id)


@pytest.mark.asyncio
async def test_change_password_revokes_refresh_tokens_and_invalidates_cache(
    user_factory,
) -> None:
    user = user_factory()
    updated_user = user_factory(id=user.id, hashed_password="new-hash")
    repo = AsyncMock()
    repo.get.return_value = user
    repo.update.return_value = updated_user
    refresh_token_repo = AsyncMock()
    password_hasher = AsyncMock()
    password_hasher.verify.return_value = True
    password_hasher.hash.return_value = "new-hash"
    password_complexity_validator = Mock()
    password_complexity_validator.get_violations.return_value = []
    invalidate_user_cache_use_case = AsyncMock()

    use_case = ChangePasswordUseCase(
        repo=repo,
        refresh_token_repo=refresh_token_repo,
        password_hasher=password_hasher,
        password_complexity_validator=password_complexity_validator,
        invalidate_user_cache_use_case=invalidate_user_cache_use_case,
        current_user=user,
    )

    result = await use_case.execute(
        ChangeUserPasswordCommand(
            id=user.id,
            old_password="old-password",
            new_password="NewStrongPass123",
        )
    )

    assert result == updated_user
    refresh_token_repo.revoke_all_for_user.assert_awaited_once_with(user.id)
    invalidate_user_cache_use_case.execute.assert_awaited_once_with(user.id)


@pytest.mark.asyncio
async def test_change_password_rejects_wrong_old_password(user_factory) -> None:
    user = user_factory()
    repo = AsyncMock()
    repo.get.return_value = user
    refresh_token_repo = AsyncMock()
    password_hasher = AsyncMock()
    password_hasher.verify.return_value = False
    password_complexity_validator = Mock()
    invalidate_user_cache_use_case = AsyncMock()

    use_case = ChangePasswordUseCase(
        repo=repo,
        refresh_token_repo=refresh_token_repo,
        password_hasher=password_hasher,
        password_complexity_validator=password_complexity_validator,
        invalidate_user_cache_use_case=invalidate_user_cache_use_case,
        current_user=user,
    )

    with pytest.raises(IncorrectPassword):
        await use_case.execute(
            ChangeUserPasswordCommand(
                id=user.id,
                old_password="wrong-password",
                new_password="NewStrongPass123",
            )
        )


@pytest.mark.asyncio
async def test_change_user_active_status_toggles_flag_for_admin(user_factory) -> None:
    admin_user = user_factory(is_admin=True)
    target_user = user_factory(is_active=True)
    updated_user = user_factory(id=target_user.id, is_active=False)
    repo = AsyncMock()
    repo.get.return_value = target_user
    repo.update.return_value = updated_user
    invalidate_user_cache_use_case = AsyncMock()

    use_case = ChangeUserActiveStatusUseCase(
        repo=repo,
        invalidate_user_cache_use_case=invalidate_user_cache_use_case,
        current_user=admin_user,
    )

    result = await use_case.execute(target_user.id)

    assert result == updated_user
    invalidate_user_cache_use_case.execute.assert_awaited_once_with(target_user.id)


@pytest.mark.asyncio
async def test_change_user_admin_status_toggles_flag_for_admin(user_factory) -> None:
    admin_user = user_factory(is_admin=True)
    target_user = user_factory(is_admin=False)
    updated_user = user_factory(id=target_user.id, is_admin=True)
    repo = AsyncMock()
    repo.get.return_value = target_user
    repo.update.return_value = updated_user
    invalidate_user_cache_use_case = AsyncMock()

    use_case = ChangeUserAdminStatusUseCase(
        repo=repo,
        invalidate_user_cache_use_case=invalidate_user_cache_use_case,
        current_user=admin_user,
    )

    result = await use_case.execute(target_user.id)

    assert result == updated_user
    invalidate_user_cache_use_case.execute.assert_awaited_once_with(target_user.id)
