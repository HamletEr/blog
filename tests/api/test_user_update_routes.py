from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from blog_app.api import middleware as middleware_module
from blog_app.api.auth_cookies import ACCESS_TOKEN_COOKIE_KEY
from blog_app.domain.exceptions.users import (
    IncorrectPassword,
    PermissionDenied,
    TooEasyPassword,
    UserNotFound,
)
from blog_app.infrastructure.dependencies.use_cases import (
    get_change_email_use_case,
    get_change_password_use_case,
    get_change_user_active_status_use_case,
    get_change_user_admin_status_use_case,
    get_change_username_use_case,
)


class DummySessionContext:
    async def __aenter__(self) -> object:
        return object()

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class DummyUserRepository:
    def __init__(self, session: object) -> None:
        self.session = session


class DummyUserCacheRepository:
    def __init__(self, redis: object, settings: object) -> None:
        self.redis = redis
        self.settings = settings


def authenticate_client(monkeypatch: pytest.MonkeyPatch, client, user) -> None:
    jwt_service = Mock()
    jwt_service.decode_token.return_value = {"sub": str(user.id)}

    class FakeResolveCurrentUserUseCase:
        def __init__(self, user_repo: object, user_cache_repo: object) -> None:
            self.user_repo = user_repo
            self.user_cache_repo = user_cache_repo

        async def execute(self, user_id):
            return user

    monkeypatch.setattr(middleware_module, "JWTService", lambda settings: jwt_service)
    monkeypatch.setattr(
        middleware_module,
        "AsyncSessionLocal",
        lambda: DummySessionContext(),
    )
    monkeypatch.setattr(middleware_module, "PGUserRepository", DummyUserRepository)
    monkeypatch.setattr(
        middleware_module,
        "RedisUserCacheRepository",
        DummyUserCacheRepository,
    )
    monkeypatch.setattr(
        middleware_module,
        "ResolveCurrentUserUseCase",
        FakeResolveCurrentUserUseCase,
    )
    client.cookies.set(
        ACCESS_TOKEN_COOKIE_KEY,
        "valid-access-token",
        domain="testserver.local",
        path="/",
    )


def test_update_username_requires_authentication(client) -> None:
    response = client.patch(
        f"/api/v1/users/{uuid4()}/username",
        json={"username": "new-name"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_update_username_returns_updated_user(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    user = user_factory()
    updated_user = user_factory(id=user.id, username="new-name")
    authenticate_client(monkeypatch, client, user)

    use_case = AsyncMock()
    use_case.execute.return_value = updated_user
    app.dependency_overrides[get_change_username_use_case] = lambda: use_case

    response = client.patch(
        f"/api/v1/users/{user.id}/username",
        json={"username": "new-name"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "new-name"
    command = use_case.execute.await_args.args[0]
    assert command.id == user.id
    assert command.username == "new-name"


def test_update_email_returns_updated_user(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    user = user_factory()
    updated_user = user_factory(id=user.id, email="new@example.com")
    authenticate_client(monkeypatch, client, user)

    use_case = AsyncMock()
    use_case.execute.return_value = updated_user
    app.dependency_overrides[get_change_email_use_case] = lambda: use_case

    response = client.patch(
        f"/api/v1/users/{user.id}/email",
        json={"email": "new@example.com", "password": "StrongPass123"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"
    command = use_case.execute.await_args.args[0]
    assert command.id == user.id
    assert command.email == "new@example.com"
    assert command.password == "StrongPass123"


def test_update_email_returns_401_for_incorrect_password(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    user = user_factory()
    authenticate_client(monkeypatch, client, user)

    use_case = AsyncMock()
    use_case.execute.side_effect = IncorrectPassword()
    app.dependency_overrides[get_change_email_use_case] = lambda: use_case

    response = client.patch(
        f"/api/v1/users/{user.id}/email",
        json={"email": "new@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect password"}


def test_update_password_returns_updated_user(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    user = user_factory()
    updated_user = user_factory(id=user.id)
    authenticate_client(monkeypatch, client, user)

    use_case = AsyncMock()
    use_case.execute.return_value = updated_user
    app.dependency_overrides[get_change_password_use_case] = lambda: use_case

    response = client.patch(
        f"/api/v1/users/{user.id}/password",
        json={
            "old_password": "OldStrongPass123",
            "new_password": "NewStrongPass123",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    command = use_case.execute.await_args.args[0]
    assert command.id == user.id
    assert command.old_password == "OldStrongPass123"
    assert command.new_password == "NewStrongPass123"


def test_update_password_returns_422_for_too_easy_password(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    user = user_factory()
    authenticate_client(monkeypatch, client, user)

    use_case = AsyncMock()
    use_case.execute.side_effect = TooEasyPassword("too short")
    app.dependency_overrides[get_change_password_use_case] = lambda: use_case

    response = client.patch(
        f"/api/v1/users/{user.id}/password",
        json={"old_password": "OldStrongPass123", "new_password": "password"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "too short"}


def test_update_user_active_status_returns_updated_user(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    admin_user = user_factory(is_admin=True)
    updated_user = user_factory(is_active=False)
    authenticate_client(monkeypatch, client, admin_user)

    use_case = AsyncMock()
    use_case.execute.return_value = updated_user
    app.dependency_overrides[get_change_user_active_status_use_case] = (
        lambda: use_case
    )

    response = client.patch(f"/api/v1/users/{updated_user.id}/status-active")

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    use_case.execute.assert_awaited_once_with(updated_user.id)


def test_update_user_admin_status_returns_403_for_permission_denied(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    user = user_factory()
    authenticate_client(monkeypatch, client, user)

    use_case = AsyncMock()
    use_case.execute.side_effect = PermissionDenied()
    app.dependency_overrides[get_change_user_admin_status_use_case] = (
        lambda: use_case
    )

    response = client.patch(f"/api/v1/users/{uuid4()}/status-admin")

    assert response.status_code == 403
    assert response.json() == {"detail": "Permission denied"}


def test_update_user_admin_status_returns_404_for_missing_user(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    admin_user = user_factory(is_admin=True)
    authenticate_client(monkeypatch, client, admin_user)

    use_case = AsyncMock()
    use_case.execute.side_effect = UserNotFound()
    app.dependency_overrides[get_change_user_admin_status_use_case] = (
        lambda: use_case
    )

    response = client.patch(f"/api/v1/users/{uuid4()}/status-admin")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
