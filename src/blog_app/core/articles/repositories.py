from abc import ABC, abstractmethod

from blog_app.core.articles.entities import Article


class ArticleRepository(ABC):
    @abstractmethod
    async def get_by_id(self, article_id: int) -> Article: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Article: ...

    @abstractmethod
    async def create(self, article: Article) -> Article: ...

    @abstractmethod
    async def update(self, article: Article) -> Article: ...

    @abstractmethod
    async def delete(self, article: Article) -> None: ...
