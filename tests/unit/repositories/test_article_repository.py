from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

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


@pytest.mark.asyncio
async def test_get_list_uses_postgres_full_text_search() -> None:
    session = AsyncMock()
    repo = PGArticleRepository(session)
    article = ArticleModel(
        id=uuid4(),
        is_active=True,
        title="Python article",
        content="Some interesting content",
        category_id=None,
        image_object_key=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.scalars.return_value = [article]

    await repo.get_list(looking_text="python fastapi", limit_on_page=10, page=1)

    stmt = session.scalars.await_args.args[0]
    compiled_query = str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )
    assert "websearch_to_tsquery('russian', 'python fastapi')" in compiled_query
    assert "@@" in compiled_query
    assert "ts_rank_cd" in compiled_query
    assert "ORDER BY" in compiled_query
