from datetime import datetime, UTC
from uuid import uuid4, UUID

import pytest

from blog_app.domain.entities.articles import Article, ArticleData
from blog_app.domain.entities.users import User
from blog_app.domain.exceptions.articles import ArticleNotFoundError
from blog_app.domain.repositories.articles import ArticleRepository


class FakeArticleRepository(ArticleRepository):
    def __init__(self) -> None:
        self._articles: dict[UUID, Article] = {}

    async def get_by_id(self, article_id: UUID) -> Article | None:
        if (article_id not in self._articles) or (
            not self._articles[article_id].is_active
        ):
            return None
        return self._articles[article_id]

    async def get_list(self, looking_text: str | None, limit: int | None) -> list[Article]:
        result = []
        for article in self._articles.values():
            if looking_text:
                article_data: ArticleData = article.data
                if (
                        looking_text.lower() in article_data.title.lower()
                        or looking_text.lower() in article_data.content.lower()
                ):
                    result.append(article)

            elif article.is_active:
                result.append(article)

            if len(result) == limit:
                break
        return result

    async def create(self, article_data: ArticleData) -> Article:
        article_id = uuid4()
        self._articles[article_id] = Article(
            id=article_id,
            is_active=True,
            data=article_data,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return self._articles[article_id]

    async def update(self, article_id: UUID, article_data: ArticleData) -> Article:
        if article_id not in self._articles:
            raise ArticleNotFoundError()
        self._articles[article_id].data = article_data
        return self._articles[article_id]

    async def delete(self, article_id: UUID) -> None:
        if article_id not in self._articles:
            raise ArticleNotFoundError()
        self._articles[article_id].is_active = False


@pytest.fixture
def repository_fixture() -> FakeArticleRepository:
    return FakeArticleRepository()


@pytest.fixture
def user_factory():
    def _create_user(is_admin: bool = False) -> User:
        return User(
            id=uuid4(),
            username="TestUser",
            email="usermail@mail.ru",
            hashed_password="hashedpassword",
            is_active=True,
            is_admin=is_admin,
        )

    return _create_user


@pytest.fixture
def article_data_factory():
    def _create_article(title: str = "test_title", content: str = "test_content"):
        return ArticleData(
            title=title,
            content=content,
            category_id=1,
            image_url="https://example.com/image.png",
        )

    return _create_article
