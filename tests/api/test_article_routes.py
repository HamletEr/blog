from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from blog_app.api import middleware as middleware_module
from blog_app.api.auth_cookies import ACCESS_TOKEN_COOKIE_KEY
from blog_app.domain.entities.articles import Article, ArticleData
from blog_app.domain.exceptions.articles import ArticleNotFoundError
from blog_app.domain.exceptions.users import PermissionDenied
from blog_app.infrastructure.dependencies.use_cases import (
    get_article_by_id_use_case,
    get_create_article_use_case,
    get_delete_article_use_case,
    get_list_articles_use_case,
    get_update_article_use_case,
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


def make_article(**kwargs) -> Article:
    return Article(
        id=kwargs.pop("id", uuid4()),
        is_active=kwargs.pop("is_active", True),
        data=kwargs.pop(
            "data",
            ArticleData(
                title="First article",
                content="Some interesting content",
                category_id=1,
                image_object_key="https://example.com/image.png",
            ),
        ),
        created_at=kwargs.pop("created_at", datetime.now(UTC)),
        updated_at=kwargs.pop("updated_at", datetime.now(UTC)),
    )


def test_articles_list_is_public_and_returns_articles(app, client) -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = [make_article()]
    app.dependency_overrides[get_list_articles_use_case] = lambda: use_case

    response = client.get("/api/v1/articles/")

    assert response.status_code == 200
    assert response.json()[0]["data"]["title"] == "First article"
    assert response.json()[0]["data"]["image_url"] == "https://example.com/image.png"


def test_articles_list_passes_query_params_to_use_case(app, client) -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = []
    app.dependency_overrides[get_list_articles_use_case] = lambda: use_case

    response = client.get(
        "/api/v1/articles/",
        params={"page": 2, "limit_on_page": 10, "looking_text": "python"},
    )

    assert response.status_code == 200
    use_case.execute.assert_awaited_once_with(
        looking_text="python",
        page=2,
        limit_on_page=10,
    )


def test_get_article_by_id_is_public(app, client) -> None:
    article = make_article()
    use_case = AsyncMock()
    use_case.execute.return_value = article
    app.dependency_overrides[get_article_by_id_use_case] = lambda: use_case

    response = client.get(f"/api/v1/articles/{article.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(article.id)
    use_case.execute.assert_awaited_once_with(article.id)


def test_get_article_by_id_returns_404_when_missing(app, client) -> None:
    article_id = uuid4()
    use_case = AsyncMock()
    use_case.execute.side_effect = ArticleNotFoundError()
    app.dependency_overrides[get_article_by_id_use_case] = lambda: use_case

    response = client.get(f"/api/v1/articles/{article_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Article not found"}


def test_create_article_requires_authentication(client) -> None:
    response = client.post(
        "/api/v1/articles/",
        json={
            "title": "First article",
            "content": "Some interesting content",
            "category_id": 1,
            "image_url": "https://example.com/image.png",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_create_article_returns_created_article(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    admin_user = user_factory(is_admin=True)
    authenticate_client(monkeypatch, client, admin_user)
    article = make_article()

    use_case = AsyncMock()
    use_case.execute.return_value = article
    app.dependency_overrides[get_create_article_use_case] = lambda: use_case

    response = client.post(
        "/api/v1/articles/",
        json={
            "title": "First article",
            "content": "Some interesting content",
            "category_id": 1,
            "image_url": "https://example.com/image.png",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(article.id)
    command = use_case.execute.await_args.args[0]
    assert command.title == "First article"
    assert command.content == "Some interesting content"
    assert command.category_id == 1
    assert command.image_object_key == "https://example.com/image.png"


def test_create_article_returns_403_for_non_admin(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    user = user_factory(is_admin=False)
    authenticate_client(monkeypatch, client, user)

    use_case = AsyncMock()
    use_case.execute.side_effect = PermissionDenied()
    app.dependency_overrides[get_create_article_use_case] = lambda: use_case

    response = client.post(
        "/api/v1/articles/",
        json={
            "title": "First article",
            "content": "Some interesting content",
            "category_id": 1,
            "image_url": "https://example.com/image.png",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Permission denied"}


def test_update_article_returns_updated_article(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    admin_user = user_factory(is_admin=True)
    authenticate_client(monkeypatch, client, admin_user)
    article = make_article()

    use_case = AsyncMock()
    use_case.execute.return_value = article
    app.dependency_overrides[get_update_article_use_case] = lambda: use_case

    response = client.put(
        f"/api/v1/articles/{article.id}",
        json={
            "title": "First article",
            "content": "Some interesting content",
            "category_id": 1,
            "image_url": "https://example.com/image.png",
        },
    )

    assert response.status_code == 202
    assert response.json()["id"] == str(article.id)
    args = use_case.execute.await_args.args
    assert args[0] == article.id
    assert args[1].title == "First article"
    assert args[1].image_object_key == "https://example.com/image.png"


def test_update_article_returns_404_when_missing(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    admin_user = user_factory(is_admin=True)
    authenticate_client(monkeypatch, client, admin_user)
    article_id = uuid4()

    use_case = AsyncMock()
    use_case.execute.side_effect = ArticleNotFoundError()
    app.dependency_overrides[get_update_article_use_case] = lambda: use_case

    response = client.put(
        f"/api/v1/articles/{article_id}",
        json={
            "title": "First article",
            "content": "Some interesting content",
            "category_id": 1,
            "image_url": "https://example.com/image.png",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Article not found"}


def test_delete_article_returns_message(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    admin_user = user_factory(is_admin=True)
    authenticate_client(monkeypatch, client, admin_user)
    article_id = uuid4()

    use_case = AsyncMock()
    app.dependency_overrides[get_delete_article_use_case] = lambda: use_case

    response = client.delete(f"/api/v1/articles/{article_id}")

    assert response.status_code == 202
    assert response.json() == {"detail": f"{article_id} deleted"}
    use_case.execute.assert_awaited_once_with(article_id)


def test_delete_article_returns_403_for_non_admin(
    app,
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    user = user_factory(is_admin=False)
    authenticate_client(monkeypatch, client, user)
    article_id = uuid4()

    use_case = AsyncMock()
    use_case.execute.side_effect = PermissionDenied()
    app.dependency_overrides[get_delete_article_use_case] = lambda: use_case

    response = client.delete(f"/api/v1/articles/{article_id}")

    assert response.status_code == 403
    assert response.json() == {"detail": "Permission denied"}


def test_articles_list_validates_looking_text_query(client) -> None:
    response = client.get("/api/v1/articles/", params={"looking_text": "ab"})

    assert response.status_code == 422


def test_create_article_validates_payload_for_authenticated_user(
    client,
    monkeypatch: pytest.MonkeyPatch,
    user_factory,
) -> None:
    admin_user = user_factory(is_admin=True)
    authenticate_client(monkeypatch, client, admin_user)

    response = client.post(
        "/api/v1/articles/",
        json={
            "title": "a",
            "content": "b",
            "category_id": 1,
            "image_url": "https://example.com/image.png",
        },
    )

    assert response.status_code == 422
