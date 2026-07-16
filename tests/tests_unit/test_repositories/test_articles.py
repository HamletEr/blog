from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from blog_app.domain.entities.articles import Article
from blog_app.infrastructure.models.articles import ArticleModel
from blog_app.infrastructure.repositories.articles import PGArticleRepository


async def test_pg_article_repository(article_model_factory):
    session = AsyncMock(AsyncSession)
    article_model = article_model_factory()

    repo = PGArticleRepository(session)

    assert isinstance(repo._model_to_domain(article_model), Article)
    assert repo._model_to_domain(article_model).id == article_model.id
