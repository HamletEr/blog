import logging
from uuid import UUID

from blog_app.domain.entities.articles import Article, ArticleData, ArticleUpdateData
from blog_app.domain.entities.files import FileToUpload
from blog_app.domain.entities.users import User
from blog_app.domain.exceptions.articles import (
    ArticleNotFoundError,
    ConflictingArticleUpdate,
    IncorrectLimitOnPage,
    IncorrectPageNumber,
    TooShortText,
)
from blog_app.domain.exceptions.object_storage import ObjectDeleteError
from blog_app.domain.repositories.articles import ArticleRepository
from blog_app.domain.services.object_storage import ObjectStorage
from blog_app.use_cases.users import get_authenticated_user, require_admin

MIN_TITLE_LENGTH = 3
MIN_CONTENT_LENGTH = 10
MIN_LOOKING_TEXT_LENGTH = 3

logger = logging.getLogger(__name__)


def validate_article_data(article_data: ArticleData) -> None:
    if len(article_data.title) < MIN_TITLE_LENGTH:
        raise TooShortText(f"Title minimal length is {MIN_TITLE_LENGTH} characters")

    if len(article_data.content) < MIN_CONTENT_LENGTH:
        raise TooShortText(f"Content minimal length is {MIN_CONTENT_LENGTH} characters")


def validate_article_update_data(
    article_data: ArticleUpdateData,
    image: FileToUpload | None = None,
) -> None:
    if article_data.title is not None and len(article_data.title) < MIN_TITLE_LENGTH:
        raise TooShortText(f"Title minimal length is {MIN_TITLE_LENGTH} characters")

    if (
        article_data.content is not None
        and len(article_data.content) < MIN_CONTENT_LENGTH
    ):
        raise TooShortText(f"Content minimal length is {MIN_CONTENT_LENGTH} characters")
    if article_data.clear_category and article_data.category_id is not None:
        raise ConflictingArticleUpdate("clear_category cannot be used with category_id")
    if article_data.clear_image and image is not None:
        raise ConflictingArticleUpdate("clear_image cannot be used with image")


def validate_looking_text(text: str) -> None:
    if len(text) < MIN_LOOKING_TEXT_LENGTH:
        raise TooShortText(
            f"Looking text minimal length is {MIN_LOOKING_TEXT_LENGTH} characters"
        )


def validate_page_and_limit_on_page(
    page: int | None, limit_on_page: int | None
) -> tuple[int | None, int | None]:
    if page and not limit_on_page:
        page = None
    if limit_on_page is not None and limit_on_page <= 0:
        raise IncorrectLimitOnPage("Limit in page must be greater than 0")
    if page is not None and page <= 0:
        raise IncorrectPageNumber("Page must be greater than 0")
    return page, limit_on_page


class BaseArticleUseCase:
    def __init__(self, repo: ArticleRepository, user: User | None) -> None:
        self.repo = repo
        self.user = user


class GetArticleById(BaseArticleUseCase):
    async def execute(self, article_id: UUID) -> Article:
        article = await self.repo.get_by_id(article_id)
        if article is None:
            raise ArticleNotFoundError()
        return article


class GetListArticles(BaseArticleUseCase):
    async def execute(
        self,
        looking_text: str | None = None,
        limit_on_page: int | None = None,
        page: int | None = None,
    ) -> list[Article]:
        if looking_text is not None:
            validate_looking_text(looking_text)
        page, limit_on_page = validate_page_and_limit_on_page(page, limit_on_page)
        return await self.repo.get_list(looking_text, limit_on_page, page)


class CreateArticle(BaseArticleUseCase):
    def __init__(
        self,
        repo: ArticleRepository,
        user: User | None,
        object_storage: ObjectStorage,
    ) -> None:
        super().__init__(repo=repo, user=user)
        self.object_storage = object_storage

    async def execute(
        self, article_data: ArticleData, image: FileToUpload | None = None
    ) -> Article:
        require_admin(get_authenticated_user(self.user))
        validate_article_data(article_data)
        if image is not None:
            stored_image = await self.object_storage.upload_file(image)
            article_data.image_object_key = stored_image.object_key
        return await self.repo.create(article_data)


class UpdateArticle(BaseArticleUseCase):
    def __init__(
        self,
        repo: ArticleRepository,
        user: User | None,
        object_storage: ObjectStorage,
    ) -> None:
        super().__init__(repo=repo, user=user)
        self.object_storage = object_storage

    async def execute(
        self,
        article_id: UUID,
        article_data: ArticleUpdateData,
        image: FileToUpload | None = None,
    ) -> Article:
        require_admin(get_authenticated_user(self.user))
        validate_article_update_data(article_data, image)
        old_image_object_key = None
        new_image_object_key = None
        if image is not None or article_data.clear_image:
            article = await self.repo.get_by_id_for_update(article_id)
            if article is None:
                raise ArticleNotFoundError()

            old_image_object_key = article.data.image_object_key

        if image is not None:
            stored_image = await self.object_storage.upload_file(image)
            new_image_object_key = stored_image.object_key
            article_data.image_object_key = stored_image.object_key
        try:
            updated_article = await self.repo.update(article_id, article_data)
        except Exception:
            if new_image_object_key is not None:
                await self._delete_uploaded_image_after_failed_update(
                    new_image_object_key, article_id
                )
            raise
        if old_image_object_key is not None:
            await self._delete_old_image(old_image_object_key, article_id)
        return updated_article

    async def _delete_old_image(self, object_key: str, article_id: UUID) -> None:
        try:
            await self.object_storage.delete_file(object_key)
        except ObjectDeleteError:
            logger.exception(
                "Failed to delete old article image",
                extra={
                    "article_id": str(article_id),
                    "image_object_key": object_key,
                },
            )

    async def _delete_uploaded_image_after_failed_update(
        self, object_key: str, article_id: UUID
    ) -> None:
        try:
            await self.object_storage.delete_file(object_key)
        except ObjectDeleteError:
            logger.exception(
                "Failed to delete uploaded article image after update failure",
                extra={
                    "article_id": str(article_id),
                    "image_object_key": object_key,
                },
            )


class DeleteArticle(BaseArticleUseCase):
    async def execute(self, article_id: UUID) -> None:
        require_admin(get_authenticated_user(self.user))
        await self.repo.delete(article_id)
