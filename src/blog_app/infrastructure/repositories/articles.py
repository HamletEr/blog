from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from blog_app.domain.entities.articles import Article, ArticleData
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
                image_url=model.image_url,
            ),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _domain_to_model(domain: Article) -> ArticleModel:
        return ArticleModel(
            id=domain.id,
            is_active=domain.is_active,
            title=domain.data.title,
            content=domain.data.content,
            category_id=domain.data.category_id,
            image_url=domain.data.image_url,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    async def get_by_id(self, article_id: UUID) -> Article | None:
        stmt = (
            select(ArticleModel)
            .where(ArticleModel.id == article_id)
            .options(joinedload(ArticleModel.category))
        )
        result = await self._session.execute(stmt)
        article: ArticleModel | None = result.scalar_one_or_none()

        return self._model_to_domain(article) if article else None

    async def get_list(
        self, looking_text: str | None, limit_on_page: int | None, page: int | None
    ) -> list[Article]:
        stmt = select(ArticleModel).options(joinedload(ArticleModel.category))
        if looking_text:
            stmt = stmt.where(
                ArticleModel.title.ilike(
                    f"%{looking_text}%"
                    or ArticleModel.content.ilike(f"%{looking_text}%")
                )
            )
        if limit_on_page:
            stmt = stmt.limit(limit_on_page)
        if page and limit_on_page:
            stmt = stmt.offset((page - 1) * limit_on_page)
        articles = await self._session.scalars(stmt)

        return [self._model_to_domain(article) for article in articles]
