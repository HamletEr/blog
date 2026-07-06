from blog_app.core.entities.articles import Article, ArticleData
from blog_app.core.entities.users import User
from blog_app.core.exceptions.articles import ArticleNotFoundError, PermissionDenied
from blog_app.core.exceptions.users import AuthenticationRequired
from blog_app.core.repositories.articles import ArticleRepository


class BaseArticleUseCase:
    def __init__(self, repo: ArticleRepository, user: User | None) -> None:
        self.repo = repo
        if user is None:
            raise AuthenticationRequired
        self.user = user


class GetArticleById(BaseArticleUseCase):
    async def execute(self, article_id: int) -> Article:
        article = await self.repo.get_by_id(article_id)
        if article is None:
            raise ArticleNotFoundError
        return article


class GetListArticles(BaseArticleUseCase):
    async def execute(self, limit: int | None = None) -> list[Article]:
        articles = await self.repo.get_list(limit)
        return articles


class GetListByText(BaseArticleUseCase):
    async def execute(self, text: str, limit: int | None = None) -> list[Article]:
        articles = await self.repo.get_list_by_text(text, limit)
        return articles


class CreateArticle(BaseArticleUseCase):
    async def execute(self, article_data: ArticleData) -> Article:
        if not self.user.is_admin:
            raise PermissionDenied
        article = await self.repo.create(article_data)
        return article


class UpdateArticle(BaseArticleUseCase):
    async def execute(self, article_id: int, article_data: ArticleData) -> Article:
        if not self.user.is_admin:
            raise PermissionDenied
        updated_article = await self.repo.update(article_id, article_data)
        return updated_article


class DeleteArticle(BaseArticleUseCase):
    async def execute(self, article_id: int) -> None:
        if not self.user.is_admin:
            raise PermissionDenied
        await self.repo.delete(article_id)
