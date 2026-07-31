from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.params import Query
from starlette import status

from blog_app.api.v1.schemas.articles import (
    ArticleDataViewSchema,
    ArticleViewSchema,
    MessageResponse,
)
from blog_app.domain.entities.articles import Article, ArticleData, ArticleUpdateData
from blog_app.domain.entities.files import FileToUpload
from blog_app.domain.services.object_storage import ObjectStorage
from blog_app.infrastructure.dependencies.services.object_storage import (
    ObjectStorageDep,
)
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


TitleForm = Annotated[str, Form(min_length=2, max_length=100)]
ContentForm = Annotated[str, Form(min_length=2, max_length=1_000_000)]
OptionalTitleForm = Annotated[str | None, Form(min_length=2, max_length=100)]
OptionalContentForm = Annotated[str | None, Form(min_length=2, max_length=1_000_000)]
CategoryIdForm = Annotated[int | None, Form(ge=1)]
ImageFile = Annotated[UploadFile | None, File()]


def map_article_to_schema(
    article: Article, object_storage: ObjectStorage
) -> ArticleViewSchema:
    image_url = None
    if article.data.image_object_key is not None:
        image_url = object_storage.get_public_url(article.data.image_object_key)

    return ArticleViewSchema(
        id=article.id,
        data=ArticleDataViewSchema.model_validate(
            {
                "title": article.data.title,
                "content": article.data.content,
                "category_id": article.data.category_id,
                "image_url": image_url,
            }
        ),
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


def map_upload_file_to_domain(file: UploadFile | None) -> FileToUpload | None:
    if file is None:
        return None

    return FileToUpload(
        filename=file.filename or "",
        content_type=file.content_type or "",
        file=file.file,
    )


@router.get("/", status_code=status.HTTP_200_OK)
async def get_articles_list(
    use_case: GetListArticlesUseCaseDep,
    object_storage: ObjectStorageDep,
    limit_on_page: Annotated[int, Query(ge=1, le=1000)] = 1000,
    page: Annotated[int | None, Query(ge=1)] = None,
    looking_text: Annotated[str | None, Query(min_length=3, max_length=100)] = None,
) -> list[ArticleViewSchema]:
    articles_domain = await use_case.execute(
        looking_text=looking_text, page=page, limit_on_page=limit_on_page
    )
    return [
        map_article_to_schema(article, object_storage) for article in articles_domain
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_article(
    use_case: CreateArticleUseCaseDep,
    object_storage: ObjectStorageDep,
    title: TitleForm,
    content: ContentForm,
    category_id: CategoryIdForm = None,
    image: ImageFile = None,
) -> ArticleViewSchema:
    article_domain = await use_case.execute(
        ArticleData(
            title=title,
            content=content,
            category_id=category_id,
            image_object_key=None,
        ),
        image=map_upload_file_to_domain(image),
    )
    return map_article_to_schema(article_domain, object_storage)


@router.get("/{article_id}", status_code=status.HTTP_200_OK)
async def get_article_by_id(
    article_id: UUID,
    use_case: GetArticleByIdUseCaseDep,
    object_storage: ObjectStorageDep,
) -> ArticleViewSchema:
    article_domain = await use_case.execute(article_id)
    return map_article_to_schema(article_domain, object_storage)


@router.patch("/{article_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_article(
    article_id: UUID,
    use_case: UpdateArticleUseCaseDep,
    object_storage: ObjectStorageDep,
    title: OptionalTitleForm = None,
    content: OptionalContentForm = None,
    category_id: CategoryIdForm = None,
    image: ImageFile = None,
) -> ArticleViewSchema:
    article_domain = await use_case.execute(
        article_id,
        ArticleUpdateData(
            title=title,
            content=content,
            category_id=category_id,
            image_object_key=None,
        ),
        image=map_upload_file_to_domain(image),
    )
    return map_article_to_schema(article_domain, object_storage)


@router.delete("/{article_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_article(
    article_id: UUID, use_case: DeleteArticleUseCaseDep
) -> MessageResponse:
    await use_case.execute(article_id)
    return MessageResponse(detail=f"{article_id} deleted")
