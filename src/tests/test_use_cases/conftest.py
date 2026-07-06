from blog_app.core.entities.articles import Article, ArticleData
from blog_app.core.exceptions.articles import ArticleNotFoundError
from blog_app.core.repositories.articles import ArticleRepository


class FakeArticleRepository(ArticleRepository):
    def __init__(self) -> None:
        self._articles: dict[int, Article] = {}
        self._next_id = 1

    def _get_next_id(self) -> int:
        next_id = self._next_id
        self._next_id += 1
        return next_id

    async def get_by_id(self, article_id: int) -> Article:
        if (article_id not in self._articles) or (
            self._articles[article_id].is_active is False
        ):
            raise ArticleNotFoundError()
        return self._articles[article_id]

    async def get_list(self, limit: int | None) -> list[Article]:
        result = []
        for article in self._articles.values():
            if article.is_active:
                result.append(article)
                if len(result) == limit:
                    break
        return result

    async def get_list_by_text(self, text: str, limit: int | None) -> list[Article]:
        result = []
        for article in self._articles.values():
            if article.is_active:
                article_data: ArticleData = article.data
                if (
                    text.lower() in article_data.title.lower()
                    or text.lower() in article_data.content.lower()
                ):
                    result.append(article)
                if len(result) == limit:
                    break
        return result

    async def create(self, article_data: ArticleData) -> Article:
        article_id = self._get_next_id()
        self._articles[article_id] = Article(
            id=article_id, is_active=True, data=article_data
        )
        return self._articles[article_id]

    async def update(self, article_id: int, article_data: ArticleData) -> Article:
        if article_id not in self._articles:
            raise ArticleNotFoundError()
        self._articles[article_id].data = article_data
        return self._articles[article_id]

    async def delete(self, article_id: int) -> None:
        if article_id not in self._articles:
            raise ArticleNotFoundError()
        self._articles[article_id].is_active = False
