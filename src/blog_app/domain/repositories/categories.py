from abc import ABC, abstractmethod

from blog_app.domain.entities.categories import Category


class CategoryArticleRepository(ABC):
    @abstractmethod
    async def get_by_id(self, category_id: int) -> Category: ...

    @abstractmethod
    async def get_list(self) -> list[Category]: ...

    @abstractmethod
    async def create(self, category_name: str) -> Category: ...
