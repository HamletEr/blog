from abc import ABC, abstractmethod
from uuid import UUID

from blog_app.domain.entities.articles import Article, ArticleData


class ArticleRepository(ABC):
    @abstractmethod
    async def get_by_id(self, article_id: UUID) -> Article | None: ...

    @abstractmethod
    async def get_list(
        self, looking_text: str | None, limit_on_page: int | None, page: int | None
    ) -> list[Article]: ...

    @abstractmethod
    async def create(self, article_data: ArticleData) -> Article: ...

    @abstractmethod
    async def update(self, article_id: UUID, article_data: ArticleData) -> Article: ...

    @abstractmethod
    async def delete(self, article_id: UUID) -> None: ...
