from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from blog_app.use_cases.cache import InvalidateUserCacheUseCase


@pytest.mark.asyncio
async def test_invalidate_user_cache_deletes_user_cache_entry() -> None:
    user_id = uuid4()
    user_cache_repo = AsyncMock()
    use_case = InvalidateUserCacheUseCase(user_cache_repo=user_cache_repo)

    await use_case.execute(user_id)

    user_cache_repo.delete.assert_awaited_once_with(user_id)
