from unittest.mock import AsyncMock, Mock

import pytest

from blog_app.api import middleware as middleware_module
from blog_app.api.auth_cookies import ACCESS_TOKEN_COOKIE_KEY
from blog_app.domain.entities.categories import Category
from blog_app.domain.exceptions.categories import (
    CategoryAlreadyExists,
    CategoryNotFound,
)
from blog_app.domain.exceptions.users import PermissionDenied
from blog_app.infrastructure.dependencies.use_cases import (
    get_by_id_category_use_case,
    get_create_category_use_case,
    get_list_categories_use_case,
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


def test_categories_list_is_public_and_returns_categories(app, client) -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = [
        Category(id=1, name="python"),
        Category(id=2, name="fastapi"),
    ]
    app.dependency_overrides[get_list_categories_use_case] = lambda: use_case

    response = client.get("/api/v1/categories/")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "python"},
        {"id": 2, "name": "fastapi"},
    ]


def test_get_category_by_id_is_public(app, client) -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = Category(id=1, name="python")
    app.dependency_overrides[get_by_id_category_use_case] = lambda: use_case

    response = client.get("/api/v1/categories/1")

    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "python"}
    use_case.execute.assert_awaited_once_with(1)


def test_create_category_requires_authentication(client) -> None:
    response = client.post("/api/v1/categories/", json={"value": "python"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_create_category_returns_created_category(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    admin_user = user_factory(is_admin=True)
    authenticate_client(monkeypatch, client, admin_user)

    use_case = AsyncMock()
    use_case.execute.return_value = Category(id=1, name="python")
    app.dependency_overrides[get_create_category_use_case] = lambda: use_case

    response = client.post("/api/v1/categories/", json={"value": "python"})

    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "python"}
    use_case.execute.assert_awaited_once_with(category_name="python")


def test_create_category_returns_403_for_non_admin(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    user = user_factory(is_admin=False)
    authenticate_client(monkeypatch, client, user)

    use_case = AsyncMock()
    use_case.execute.side_effect = PermissionDenied()
    app.dependency_overrides[get_create_category_use_case] = lambda: use_case

    response = client.post("/api/v1/categories/", json={"value": "python"})

    assert response.status_code == 403
    assert response.json() == {"detail": "Permission denied"}


def test_create_category_returns_409_for_duplicate(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    admin_user = user_factory(is_admin=True)
    authenticate_client(monkeypatch, client, admin_user)

    use_case = AsyncMock()
    use_case.execute.side_effect = CategoryAlreadyExists()
    app.dependency_overrides[get_create_category_use_case] = lambda: use_case

    response = client.post("/api/v1/categories/", json={"value": "python"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Category already exists"}


def test_get_category_by_id_returns_404_when_missing(app, client) -> None:
    use_case = AsyncMock()
    use_case.execute.side_effect = CategoryNotFound()
    app.dependency_overrides[get_by_id_category_use_case] = lambda: use_case

    response = client.get("/api/v1/categories/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}


def test_create_category_validates_payload(
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    admin_user = user_factory(is_admin=True)
    authenticate_client(monkeypatch, client, admin_user)

    response = client.post("/api/v1/categories/", json={"value": "x"})

    assert response.status_code == 422
