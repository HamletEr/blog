from uuid import UUID

from blog_app.domain.repositories.user_cache import UserCacheRepository


class InvalidateUserCacheUseCase:
    def __init__(self, user_cache_repo: UserCacheRepository) -> None:
        self.user_cache_repo = user_cache_repo

    async def execute(self, user_id: UUID) -> None:
        await self.user_cache_repo.delete(user_id)
