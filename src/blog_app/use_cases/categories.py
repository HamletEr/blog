from blog_app.domain.entities.categories import Category
from blog_app.domain.entities.users import User
from blog_app.domain.repositories.categories import CategoryArticleRepository
from blog_app.use_cases.users import get_authenticated_user, require_admin


class BaseCategoryArticleUseCase:
    def __init__(self, repo: CategoryArticleRepository, user: User):
        self.repo = repo
        self.user = get_authenticated_user(user)


class CreateCategoryArticleUseCase(BaseCategoryArticleUseCase):
    async def execute(self, category_name: str) -> Category:
        require_admin(self.user)
        return await self.repo.create(category_name)


class GetListCategoryArticleUseCase(BaseCategoryArticleUseCase):
    async def execute(self) -> list[Category]:
        return await self.repo.get_list()


class GetByIdCategoryArticleUseCase(BaseCategoryArticleUseCase):
    async def execute(self, category_id: int) -> Category:
        return await self.repo.get_by_id(category_id)
