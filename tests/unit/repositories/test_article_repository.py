from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from blog_app.domain.entities.articles import ArticleUpdateData
from blog_app.infrastructure.models.articles import ArticleModel
from blog_app.infrastructure.repositories.articles import PGArticleRepository


@pytest.mark.asyncio
async def test_update_article_can_clear_nullable_fields() -> None:
    session = AsyncMock()
    repo = PGArticleRepository(session)
    article_id = uuid4()
    article = ArticleModel(
        id=article_id,
        is_active=True,
        title="First article",
        content="Some interesting content",
        category_id=1,
        image_object_key="articles/images/20260731/image.png",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repo._get_model_by_id = AsyncMock(return_value=article)  # type: ignore[method-assign]

    updated_article = await repo.update(
        article_id,
        ArticleUpdateData(clear_category=True, clear_image=True),
    )

    assert article.category_id is None
    assert article.image_object_key is None
    assert updated_article.data.category_id is None
    assert updated_article.data.image_object_key is None
    session.flush.assert_awaited_once()
