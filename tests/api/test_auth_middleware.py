from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from blog_app.api import middleware as middleware_module
from blog_app.domain.entities.articles import Article, ArticleData
from blog_app.domain.entities.categories import Category
from blog_app.domain.exceptions.tokens import ExpiredToken, InvalidToken
from blog_app.domain.exceptions.users import PermissionDenied, UserNotFound
from blog_app.infrastructure.dependencies.use_cases import (
    get_list_articles_use_case,
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


def patch_auth_middleware_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    *,
    jwt_payload: dict[str, str] | None = None,
    jwt_error: Exception | None = None,
    resolved_user=None,
    resolve_error: Exception | None = None,
) -> None:
    jwt_service = Mock()
    if jwt_error is not None:
        jwt_service.decode_token.side_effect = jwt_error
    else:
        jwt_service.decode_token.return_value = jwt_payload or {"sub": str(uuid4())}

    class FakeResolveCurrentUserUseCase:
        def __init__(self, user_repo: object, user_cache_repo: object) -> None:
            self.user_repo = user_repo
            self.user_cache_repo = user_cache_repo

        async def execute(self, user_id):
            if resolve_error is not None:
                raise resolve_error
            return resolved_user

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


def test_protected_route_requires_access_token(client) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_protected_route_returns_401_for_invalid_access_token(
    monkeypatch: pytest.MonkeyPatch,
    client,
) -> None:
    patch_auth_middleware_dependencies(
        monkeypatch,
        jwt_error=InvalidToken(),
    )
    client.cookies.set(
        "access_token",
        "broken-access-token",
        domain="testserver.local",
        path="/",
    )

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_protected_route_returns_401_for_expired_access_token(
    monkeypatch: pytest.MonkeyPatch,
    client,
) -> None:
    patch_auth_middleware_dependencies(
        monkeypatch,
        jwt_error=ExpiredToken(),
    )
    client.cookies.set(
        "access_token",
        "expired-access-token",
        domain="testserver.local",
        path="/",
    )

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


@pytest.mark.parametrize("error", [PermissionDenied(), UserNotFound()])
def test_protected_route_returns_401_when_current_user_cannot_be_resolved(
    monkeypatch: pytest.MonkeyPatch,
    client,
    error,
) -> None:
    patch_auth_middleware_dependencies(
        monkeypatch,
        jwt_payload={"sub": str(uuid4())},
        resolve_error=error,
    )
    client.cookies.set(
        "access_token",
        "valid-access-token",
        domain="testserver.local",
        path="/",
    )

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_auth_me_returns_current_user_for_valid_access_token(
    monkeypatch: pytest.MonkeyPatch,
    client,
    user_factory,
) -> None:
    user = user_factory()
    patch_auth_middleware_dependencies(
        monkeypatch,
        jwt_payload={"sub": str(user.id)},
        resolved_user=user,
    )
    client.cookies.set(
        "access_token",
        "valid-access-token",
        domain="testserver.local",
        path="/",
    )

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    assert response.json()["email"] == user.email


def test_health_live_is_public(client) -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_categories_list_is_public(app, client) -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = [Category(id=1, name="python")]
    app.dependency_overrides[get_list_categories_use_case] = lambda: use_case

    response = client.get("/api/v1/categories/")

    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "python"}]


def test_articles_list_is_public(app, client) -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = [
        Article(
            id=uuid4(),
            is_active=True,
            data=ArticleData(
                title="First article",
                content="Some content",
                category_id=1,
                image_url="https://example.com/image.png",
            ),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    ]
    app.dependency_overrides[get_list_articles_use_case] = lambda: use_case

    response = client.get("/api/v1/articles/")

    assert response.status_code == 200
    assert response.json()[0]["data"]["title"] == "First article"
