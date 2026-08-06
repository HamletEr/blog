from blog_app.domain.entities.categories import Category
from blog_app.domain.entities.users import User
from blog_app.domain.repositories.categories import CategoryRepository
from blog_app.use_cases.users import get_authenticated_user, require_admin


class BaseCategoryUseCase:
    def __init__(self, repo: CategoryRepository, user: User | None):
        self.repo = repo
        self.user = user


class CreateCategoryUseCase(BaseCategoryUseCase):
    async def execute(self, category_name: str) -> Category:
        require_admin(get_authenticated_user(self.user))
        return await self.repo.create(category_name)


class GetListCategoryUseCase(BaseCategoryUseCase):
    async def execute(self) -> list[Category]:
        return await self.repo.get_list()


class GetByIdCategoryUseCase(BaseCategoryUseCase):
    async def execute(self, category_id: int) -> Category:
        return await self.repo.get_by_id(category_id)
