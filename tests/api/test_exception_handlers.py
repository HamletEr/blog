from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from blog_app.api import middleware as middleware_module
from blog_app.api.auth_cookies import ACCESS_TOKEN_COOKIE_KEY
from blog_app.domain.exceptions.articles import ArticleNotFoundError
from blog_app.domain.exceptions.categories import (
    CategoryAlreadyExists,
    CategoryNotFound,
)
from blog_app.domain.exceptions.users import (
    EmailAlreadyExists,
    TooEasyPassword,
    UserAlreadyExists,
)
from blog_app.infrastructure.dependencies.use_cases import (
    get_article_by_id_use_case,
    get_by_id_category_use_case,
    get_change_email_use_case,
    get_change_password_use_case,
    get_create_category_use_case,
    get_register_and_issue_tokens_use_case,
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


def test_user_already_exists_maps_to_409(app, client) -> None:
    use_case = AsyncMock()
    use_case.execute.side_effect = UserAlreadyExists("alice@example.com")
    app.dependency_overrides[get_register_and_issue_tokens_use_case] = (
        lambda: use_case
    )

    response = client.post(
        "/api/v1/users/",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "StrongPass123",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "alice@example.com"}


def test_email_already_exists_maps_to_409(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    user = user_factory()
    authenticate_client(monkeypatch, client, user)
    use_case = AsyncMock()
    use_case.execute.side_effect = EmailAlreadyExists("new@example.com")
    app.dependency_overrides[get_change_email_use_case] = lambda: use_case

    response = client.patch(
        f"/api/v1/users/{user.id}/email",
        json={"email": "new@example.com", "password": "StrongPass123"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "new@example.com"}


def test_too_easy_password_maps_to_422(
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
        json={
            "old_password": "OldStrongPass123",
            "new_password": "password",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "too short"}


def test_category_already_exists_maps_to_409(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    user = user_factory()
    authenticate_client(monkeypatch, client, user)
    use_case = AsyncMock()
    use_case.execute.side_effect = CategoryAlreadyExists()
    app.dependency_overrides[get_create_category_use_case] = lambda: use_case

    response = client.post("/api/v1/categories/", json={"value": "python"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Category already exists"}


def test_category_not_found_maps_to_404(app, client) -> None:
    use_case = AsyncMock()
    use_case.execute.side_effect = CategoryNotFound()
    app.dependency_overrides[get_by_id_category_use_case] = lambda: use_case

    response = client.get("/api/v1/categories/1")

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}


def test_article_not_found_maps_to_404(app, client) -> None:
    article_id = uuid4()
    use_case = AsyncMock()
    use_case.execute.side_effect = ArticleNotFoundError()
    app.dependency_overrides[get_article_by_id_use_case] = lambda: use_case

    response = client.get(f"/api/v1/articles/{article_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Article not found"}
