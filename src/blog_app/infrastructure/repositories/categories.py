from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from blog_app.domain.entities.categories import Category
from blog_app.domain.exceptions.categories import (
    CategoryAlreadyExists,
    CategoryNotFound,
)
from blog_app.domain.repositories.categories import CategoryRepository
from blog_app.infrastructure.models.categories import CategoryModel


class PGCategoryRepository(CategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _model_to_domain(model: CategoryModel) -> Category:
        return Category(
            id=model.id,
            name=model.name,
        )

    async def get_by_id(self, category_id: int) -> Category:
        stmt = select(CategoryModel).where(CategoryModel.id == category_id)
        result: CategoryModel | None = (
            await self._session.execute(stmt)
        ).scalar_one_or_none()
        if result is None:
            raise CategoryNotFound()
        return self._model_to_domain(result)

    async def get_list(self) -> list[Category]:
        stmt = select(CategoryModel)
        categories = await self._session.scalars(stmt)
        return [self._model_to_domain(category) for category in categories]

    async def create(self, category_name: str) -> Category:
        category = CategoryModel(name=category_name)
        try:
            self._session.add(category)
            await self._session.flush()
            return self._model_to_domain(category)
        except IntegrityError as exc:
            raise CategoryAlreadyExists() from exc
