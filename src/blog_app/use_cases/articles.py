from blog_app.core.entities.articles import Article, ArticleData
from blog_app.core.entities.users import User
from blog_app.core.exceptions.articles import (
    ArticleNotFoundError,
    FragmentIsTooShortToSearch,
    PermissionDenied,
)
from blog_app.core.exceptions.users import AuthenticationRequired
from blog_app.core.repositories.articles import ArticleRepository


class BaseArticleUseCase:
    def __init__(self, repo: ArticleRepository, user: User | None) -> None:
        self.repo = repo
        if user is None:
            raise AuthenticationRequired
        self.user = user

    def _permission_required(self) -> None:
        if not self.user.is_admin:
            raise PermissionDenied


class GetArticleById(BaseArticleUseCase):
    async def execute(self, article_id: int) -> Article:
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
            raise FragmentIsTooShortToSearch
        return await self.repo.get_list_by_text(text, limit)


class CreateArticle(BaseArticleUseCase):
    async def execute(self, article_data: ArticleData) -> Article:
        self._permission_required()
        return await self.repo.create(article_data)


class UpdateArticle(BaseArticleUseCase):
    async def execute(self, article_id: int, article_data: ArticleData) -> Article:
        self._permission_required()
        updated_article = await self.repo.update(article_id, article_data)
        return updated_article


class DeleteArticle(BaseArticleUseCase):
    async def execute(self, article_id: int) -> None:
        self._permission_required()
        await self.repo.delete(article_id)
