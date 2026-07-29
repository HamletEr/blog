from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi.params import Query
from starlette import status

from blog_app.api.v1.schemas.articles import (
    ArticleDataSchema,
    ArticleViewSchema,
    MessageResponse,
)
from blog_app.domain.entities.articles import ArticleData
from blog_app.infrastructure.dependencies.use_cases import (
    CreateArticleUseCaseDep,
    DeleteArticleUseCaseDep,
    GetArticleByIdUseCaseDep,
    GetListArticlesUseCaseDep,
    UpdateArticleUseCaseDep,
)

router = APIRouter(
    prefix="/articles",
    tags=["articles"],
)


@router.get("/", status_code=status.HTTP_200_OK)
async def get_articles_list(
    use_case: GetListArticlesUseCaseDep,
    limit_on_page: Annotated[int, Query(ge=1, le=1000)] = 1000,
    page: Annotated[int | None, Query(ge=1)] = None,
    looking_text: Annotated[str | None, Query(min_length=3, max_length=100)] = None,
) -> list[ArticleViewSchema]:
    articles_domain = await use_case.execute(
        looking_text=looking_text, page=page, limit_on_page=limit_on_page
    )
    return list(
        ArticleViewSchema.model_validate(article) for article in articles_domain
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_article(
    article_data: ArticleDataSchema, use_case: CreateArticleUseCaseDep
) -> ArticleViewSchema:
    article_domain = await use_case.execute(
        ArticleData(
            title=article_data.title,
            content=article_data.content,
            category_id=article_data.category_id,
            image_url=(
                str(article_data.image_url)
                if article_data.image_url is not None
                else None
            ),
        )
    )
    return ArticleViewSchema.model_validate(article_domain)


@router.get("/{article_id}", status_code=status.HTTP_200_OK)
async def get_article_by_id(
    article_id: UUID, use_case: GetArticleByIdUseCaseDep
) -> ArticleViewSchema:
    article_domain = await use_case.execute(article_id)
    return ArticleViewSchema.model_validate(article_domain)


@router.put("/{article_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_article(
    article_id: UUID,
    article_data: ArticleDataSchema,
    use_case: UpdateArticleUseCaseDep,
) -> ArticleViewSchema:
    article_domain = await use_case.execute(
        article_id,
        ArticleData(
            title=article_data.title,
            content=article_data.content,
            category_id=article_data.category_id,
            image_url=(
                str(article_data.image_url)
                if article_data.image_url is not None
                else None
            ),
        ),
    )
    return ArticleViewSchema.model_validate(article_domain)


@router.delete("/{article_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_article(
    article_id: UUID, use_case: DeleteArticleUseCaseDep
) -> MessageResponse:
    await use_case.execute(article_id)
    return MessageResponse(detail=f"{article_id} deleted")
