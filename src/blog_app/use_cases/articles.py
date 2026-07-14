from uuid import UUID

from blog_app.domain.entities.articles import Article, ArticleData
from blog_app.domain.entities.users import User
from blog_app.domain.exceptions.articles import (
    ArticleNotFoundError,
    IncorrectLimitOnPage,
    IncorrectPageNumber,
    PermissionDenied,
    TooShortText,
)
from blog_app.domain.exceptions.users import AuthenticationRequired
from blog_app.domain.repositories.articles import ArticleRepository

MIN_TITLE_LENGTH = 3
MIN_CONTENT_LENGTH = 10
MIN_LOOKING_TEXT_LENGTH = 3


def require_authenticated(user: User | None) -> User:
    if user is None:
        raise AuthenticationRequired
    return user


def require_admin(user: User) -> None:
    if not user.is_admin:
        raise PermissionDenied


def validate_article_data(article_data: ArticleData) -> None:
    if len(article_data.title) < MIN_TITLE_LENGTH:
        raise TooShortText(f"Title minimal length is {MIN_TITLE_LENGTH} characters")

    if len(article_data.content) < MIN_CONTENT_LENGTH:
        raise TooShortText(f"Content minimal length is {MIN_CONTENT_LENGTH} characters")


def validate_looking_text(text: str) -> None:
    if len(text) < MIN_LOOKING_TEXT_LENGTH:
        raise TooShortText(
            f"Looking text minimal length is {MIN_LOOKING_TEXT_LENGTH} characters"
        )


def validate_page_and_limit_on_page(
    page: int | None, limit_on_page: int | None
) -> tuple[int | None, int | None]:
    if page and not limit_on_page:
        page = None
    if limit_on_page is not None and limit_on_page <= 0:
        raise IncorrectLimitOnPage("Limit in page must be greater than 0")
    if page is not None and page <= 0:
        raise IncorrectPageNumber("Page must be greater than 0")
    return page, limit_on_page


class BaseArticleUseCase:
    def __init__(self, repo: ArticleRepository, user: User | None) -> None:
        self.repo = repo
        self.user = require_authenticated(user)


class GetArticleById(BaseArticleUseCase):
    async def execute(self, article_id: UUID) -> Article:
        article = await self.repo.get_by_id(article_id)
        if article is None:
            raise ArticleNotFoundError()
        return article


class GetListArticles(BaseArticleUseCase):
    async def execute(
        self,
        looking_text: str | None = None,
        limit_on_page: int | None = None,
        page: int | None = None,
    ) -> list[Article]:
        if looking_text is not None:
            validate_looking_text(looking_text)
        page, limit_on_page = validate_page_and_limit_on_page(page, limit_on_page)
        return await self.repo.get_list(looking_text, limit_on_page, page)


class CreateArticle(BaseArticleUseCase):
    async def execute(self, article_data: ArticleData) -> Article:
        require_admin(self.user)
        validate_article_data(article_data)
        return await self.repo.create(article_data)


class UpdateArticle(BaseArticleUseCase):
    async def execute(self, article_id: UUID, article_data: ArticleData) -> Article:
        require_admin(self.user)
        validate_article_data(article_data)
        updated_article = await self.repo.update(article_id, article_data)
        return updated_article


class DeleteArticle(BaseArticleUseCase):
    async def execute(self, article_id: UUID) -> None:
        require_admin(self.user)
        await self.repo.delete(article_id)
