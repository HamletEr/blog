from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

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
    UserAlreadyExists,
    UserNotFound,
)
from blog_app.domain.repositories.users import UserRepository
from blog_app.domain.services.passwords import PasswordHasher
from blog_app.use_cases.users import (
    ChangeEmailUseCase,
    ChangePasswordUseCase,
    ChangeUserActiveStatusUseCase,
    ChangeUsernameUseCase,
    CreateUserUseCase,
    LoginUserUseCase,
    check_user_can_modify_user,
    get_authenticated_user,
)

VALID_PASSWORD = "dfkjgJDHF_g324"
OLD_HASHED_PASSWORD = "old_hash"
NEW_HASHED_PASSWORD = "new_hash"


def make_user(
    *,
    is_admin: bool = False,
    is_active: bool = True,
    hashed_password: str = OLD_HASHED_PASSWORD,
    email: str = "user@mail.ru",
) -> User:
    return User(
        id=uuid4(),
        username="Ivan",
        email=email,
        hashed_password=hashed_password,
        is_active=is_active,
        is_admin=is_admin,
        registered_at=None,
    )


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def password_service() -> AsyncMock:
    return AsyncMock(spec=PasswordHasher)


def test_get_authenticated_user():
    user = make_user()

    with pytest.raises(AuthenticationRequired):
        get_authenticated_user(user=None)

    assert get_authenticated_user(user) == user


def test_check_user_can_modify_user():
    common_user = make_user(is_admin=False)

    with pytest.raises(PermissionDenied):
        check_user_can_modify_user(current_user=common_user, modified_user_id=uuid4())

    assert check_user_can_modify_user(current_user=common_user, modified_user_id=common_user.id) is None

    admin_user = make_user(is_admin=True)

    assert check_user_can_modify_user(current_user=admin_user, modified_user_id=uuid4()) is None


async def test_create_user(repo: AsyncMock, password_service: AsyncMock):
    user_data = CreateUserCommand(
        username="Ivan",
        email="e@mail.ru",
        password=VALID_PASSWORD,
    )
    created_user = make_user(email=user_data.email, hashed_password=NEW_HASHED_PASSWORD)
    repo.get.return_value = None
    repo.create.return_value = created_user
    password_service.hash.return_value = NEW_HASHED_PASSWORD

    result = await CreateUserUseCase(repo=repo).execute(user_data, password_service)

    assert result == created_user
    repo.get.assert_awaited_once_with(user_email=user_data.email)
    password_service.hash.assert_awaited_once_with(user_data.password)
    repo.create.assert_awaited_once()

    raw_user = repo.create.await_args.args[0]
    assert raw_user.id is None
    assert raw_user.username == user_data.username
    assert raw_user.email == user_data.email
    assert raw_user.hashed_password == NEW_HASHED_PASSWORD
    assert raw_user.is_active is True
    assert raw_user.is_admin is False


async def test_create_user_raises_if_email_already_exists(
    repo: AsyncMock, password_service: AsyncMock
):
    existing_user = make_user(email="e@mail.ru")
    repo.get.return_value = existing_user
    user_data = CreateUserCommand(
        username="Ivan",
        email=existing_user.email,
        password=VALID_PASSWORD,
    )

    with pytest.raises(UserAlreadyExists):
        await CreateUserUseCase(repo=repo).execute(user_data, password_service)

    repo.get.assert_awaited_once_with(user_email=user_data.email)
    password_service.hash.assert_not_awaited()
    repo.create.assert_not_awaited()


async def test_login_user(repo: AsyncMock, password_service: AsyncMock):
    user = make_user(hashed_password=OLD_HASHED_PASSWORD)
    user_data = LoginUserCommand(email=user.email, password=VALID_PASSWORD)
    repo.get.return_value = user
    password_service.verify.return_value = True

    result = await LoginUserUseCase(repo=repo).execute(user_data, password_service)

    assert result == user
    repo.get.assert_awaited_once_with(user_email=user_data.email)
    password_service.verify.assert_awaited_once_with(
        user_data.password, OLD_HASHED_PASSWORD
    )


async def test_login_user_raises_if_user_not_found(
    repo: AsyncMock, password_service: AsyncMock
):
    repo.get.return_value = None
    user_data = LoginUserCommand(email="missing@mail.ru", password=VALID_PASSWORD)

    with pytest.raises(UserNotFound):
        await LoginUserUseCase(repo=repo).execute(user_data, password_service)

    repo.get.assert_awaited_once_with(user_email=user_data.email)
    password_service.verify.assert_not_awaited()


async def test_login_user_raises_if_password_is_incorrect(
    repo: AsyncMock, password_service: AsyncMock
):
    user = make_user(hashed_password=OLD_HASHED_PASSWORD)
    user_data = LoginUserCommand(email=user.email, password="wrong-password")
    repo.get.return_value = user
    password_service.verify.return_value = False

    with pytest.raises(UserNotFound):
        await LoginUserUseCase(repo=repo).execute(user_data, password_service)

    password_service.verify.assert_awaited_once_with(
        user_data.password, OLD_HASHED_PASSWORD
    )


async def test_change_username(repo: AsyncMock):
    user = make_user()
    user_data = ChangeUserUsernameCommand(id=user.id, username="new_username")
    repo.get.return_value = user
    repo.update.side_effect = lambda updated_user: updated_user

    result = await ChangeUsernameUseCase(repo, user).execute(user_data)

    assert result == user
    assert result.username == user_data.username
    repo.get.assert_awaited_once_with(user_id=user_data.id)
    repo.update.assert_awaited_once_with(user)


async def test_change_username_raises_if_user_cannot_modify(repo: AsyncMock):
    current_user = make_user(is_admin=False)
    user_data = ChangeUserUsernameCommand(id=uuid4(), username="new_username")

    with pytest.raises(PermissionDenied):
        await ChangeUsernameUseCase(repo, current_user).execute(user_data)

    repo.get.assert_not_awaited()
    repo.update.assert_not_awaited()


async def test_change_username_raises_if_user_not_found(repo: AsyncMock):
    admin_user = make_user(is_admin=True)
    user_data = ChangeUserUsernameCommand(id=uuid4(), username="new_username")
    repo.get.return_value = None

    with pytest.raises(UserNotFound):
        await ChangeUsernameUseCase(repo, admin_user).execute(user_data)

    repo.update.assert_not_awaited()


async def test_change_email(repo: AsyncMock, password_service: AsyncMock):
    user = make_user(hashed_password=OLD_HASHED_PASSWORD)
    user_data = ChangeUserEmailCommand(
        id=user.id,
        email="new@mail.ru",
        password=VALID_PASSWORD,
    )
    password_service.verify.return_value = True

    async def get_user_by_id_or_email(user_id=None, user_email=None):
        if user_id == user.id:
            return user
        if user_email == user_data.email:
            return None
        return None

    repo.get.side_effect = get_user_by_id_or_email
    repo.update.side_effect = lambda updated_user: updated_user

    result = await ChangeEmailUseCase(repo, user).execute(user_data, password_service)

    assert result == user
    assert result.email == user_data.email
    password_service.verify.assert_awaited_once_with(
        user_data.password, OLD_HASHED_PASSWORD
    )
    repo.update.assert_awaited_once_with(user)


async def test_change_email_raises_if_password_is_incorrect(
    repo: AsyncMock, password_service: AsyncMock
):
    user = make_user(hashed_password=OLD_HASHED_PASSWORD)
    user_data = ChangeUserEmailCommand(
        id=user.id,
        email="new@mail.ru",
        password="wrong-password",
    )
    repo.get.return_value = user
    password_service.verify.return_value = False

    with pytest.raises(IncorrectPassword):
        await ChangeEmailUseCase(repo, user).execute(user_data, password_service)

    repo.update.assert_not_awaited()


async def test_change_email_raises_if_email_already_exists(
    repo: AsyncMock, password_service: AsyncMock
):
    user = make_user(hashed_password=OLD_HASHED_PASSWORD)
    existing_user = make_user(email="new@mail.ru")
    user_data = ChangeUserEmailCommand(
        id=user.id,
        email=existing_user.email,
        password=VALID_PASSWORD,
    )
    password_service.verify.return_value = True

    async def get_user_by_id_or_email(user_id=None, user_email=None):
        if user_id == user.id:
            return user
        if user_email == existing_user.email:
            return existing_user
        return None

    repo.get.side_effect = get_user_by_id_or_email

    with pytest.raises(EmailAlreadyExists):
        await ChangeEmailUseCase(repo, user).execute(user_data, password_service)

    repo.update.assert_not_awaited()
