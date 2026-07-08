from typing import Any
from uuid import UUID

from blog_app.domain.entities.articles import Article, ArticleData
from blog_app.domain.entities.users import User
from blog_app.domain.exceptions.articles import (
    ArticleNotFoundError,
    PermissionDenied,
    TooShortText,
)
from blog_app.domain.exceptions.users import AuthenticationRequired
from blog_app.domain.repositories.articles import ArticleRepository


class BaseArticleUseCase:
    def __init__(self, repo: ArticleRepository, user: User | None) -> None:
        self.repo = repo
        if user is None:
            raise AuthenticationRequired
        self.user = user


class ChangeArticleData(BaseArticleUseCase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.min_title_length = 3
        self.min_content_length = 10

    def _permission_required(self) -> None:
        if not self.user.is_admin:
            raise PermissionDenied

    def _check_fields_length(self, article_data: ArticleData) -> None:
        title_length = len(article_data.title)
        content_length = len(article_data.content)

        if title_length < self.min_title_length:
            raise TooShortText(
                f"Title minimal length is {self.min_title_length} characters"
            )

        if content_length < self.min_content_length:
            raise TooShortText(
                f"Content minimal length is {self.min_content_length} characters"
            )


class GetArticleById(BaseArticleUseCase):
    async def execute(self, article_id: UUID) -> Article:
        article = await self.repo.get_by_id(article_id)
        if article is None:
            raise ArticleNotFoundError
        return article


class GetListArticles(BaseArticleUseCase):
    async def execute(self, limit: int | None = None) -> list[Article]:
        return await self.repo.get_list(limit)


class GetListByText(BaseArticleUseCase):
    async def execute(self, text: str, limit: int | None = None) -> list[Article]:
        if len(text) <= 3:
            raise TooShortText
        return await self.repo.get_list_by_text(text, limit)


class CreateArticleData(ChangeArticleData):
    async def execute(self, article_data: ArticleData) -> Article:
        self._permission_required()
        self._check_fields_length(article_data)
        return await self.repo.create(article_data)


class UpdateArticleData(ChangeArticleData):
    async def execute(self, article_id: UUID, article_data: ArticleData) -> Article:
        self._permission_required()
        self._check_fields_length(article_data)
        updated_article = await self.repo.update(article_id, article_data)
        return updated_article


class DeleteArticleData(ChangeArticleData):
    async def execute(self, article_id: UUID) -> None:
        self._permission_required()
        await self.repo.delete(article_id)
