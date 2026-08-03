from dataclasses import asdict
from uuid import UUID

from sqlalchemy import desc, func, literal_column, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from blog_app.domain.entities.articles import Article, ArticleData, ArticleUpdateData
from blog_app.domain.exceptions.articles import ArticleNotFoundError
from blog_app.domain.repositories.articles import ArticleRepository
from blog_app.infrastructure.models.articles import ArticleModel


class PGArticleRepository(ArticleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _model_to_domain(model: ArticleModel) -> Article:
        return Article(
            id=model.id,
            is_active=model.is_active,
            data=ArticleData(
                title=model.title,
                content=model.content,
                category_id=model.category_id,
                image_object_key=model.image_object_key,
            ),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def _get_model_by_id(self, article_id: UUID) -> ArticleModel | None:
        stmt = select(ArticleModel).where(
            ArticleModel.id == article_id, ArticleModel.is_active.is_(True)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_model_by_id_for_update(
        self, article_id: UUID
    ) -> ArticleModel | None:
        stmt = (
            select(ArticleModel)
            .where(
                ArticleModel.id == article_id,
                ArticleModel.is_active == true(),
            )
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, article_id: UUID) -> Article | None:
        article = await self._get_model_by_id(article_id)

        return self._model_to_domain(article) if article else None

    async def get_by_id_for_update(self, article_id: UUID) -> Article | None:
        article = await self._get_model_by_id_for_update(article_id)

        return self._model_to_domain(article) if article else None

    async def get_list(
        self, looking_text: str | None, limit_on_page: int | None, page: int | None
    ) -> list[Article]:
        stmt = select(ArticleModel).where(ArticleModel.is_active == true())
        if looking_text:
            search_query = func.websearch_to_tsquery(
                literal_column("'russian'"), looking_text
            )
            rank = func.ts_rank_cd(ArticleModel.search_vector, search_query)
            stmt = stmt.where(
                ArticleModel.search_vector.op("@@")(search_query)
            ).order_by(desc(rank), ArticleModel.created_at.desc())
        if limit_on_page:
            stmt = stmt.limit(limit_on_page)
        if page and limit_on_page:
            stmt = stmt.offset((page - 1) * limit_on_page)
        articles = await self._session.scalars(stmt)

        return [self._model_to_domain(article) for article in articles]

    async def create(self, article_data: ArticleData) -> Article:
        article = ArticleModel(**asdict(article_data))
        self._session.add(article)
        await self._session.flush()

        return self._model_to_domain(article)

    async def update(
        self, article_id: UUID, article_data: ArticleUpdateData
    ) -> Article:
        article = await self._get_model_by_id(article_id)
        if not article:
            raise ArticleNotFoundError()

        if article_data.title is not None:
            article.title = article_data.title
        if article_data.content is not None:
            article.content = article_data.content
        if article_data.clear_category or article_data.category_id is not None:
            article.category_id = article_data.category_id
        if article_data.clear_image or article_data.image_object_key is not None:
            article.image_object_key = article_data.image_object_key

        await self._session.flush()
        return self._model_to_domain(article)

    async def delete(self, article_id: UUID) -> None:
        article = await self._get_model_by_id(article_id)
        if not article:
            raise ArticleNotFoundError()
        article.is_active = False
        await self._session.flush()
