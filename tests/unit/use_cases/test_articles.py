from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from blog_app.domain.entities.articles import Article, ArticleData, ArticleUpdateData
from blog_app.domain.entities.files import FileToUpload, StoredObject
from blog_app.use_cases.articles import CreateArticle, UpdateArticle


def make_article(article_data: ArticleData) -> Article:
    return Article(
        id=uuid4(),
        is_active=True,
        data=article_data,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_create_article_uploads_image_and_saves_object_key(
    user_factory,
) -> None:
    user = user_factory(is_admin=True)
    repo = AsyncMock()
    object_storage = AsyncMock()
    object_storage.upload_file.return_value = StoredObject(
        object_key="articles/images/20260731/image.png"
    )
    repo.create.side_effect = make_article
    use_case = CreateArticle(
        repo=repo,
        user=user,
        object_storage=object_storage,
    )
    article_data = ArticleData(
        title="First article",
        content="Some interesting content",
        category_id=1,
        image_object_key=None,
    )
    image = FileToUpload(
        filename="image.png",
        content_type="image/png",
        file=BytesIO(b"content"),
    )

    article = await use_case.execute(article_data, image=image)

    object_storage.upload_file.assert_awaited_once_with(image)
    saved_article_data = repo.create.await_args.args[0]
    assert saved_article_data.image_object_key == "articles/images/20260731/image.png"
    assert article.data.image_object_key == "articles/images/20260731/image.png"


@pytest.mark.asyncio
async def test_create_article_without_image_saves_none(user_factory) -> None:
    user = user_factory(is_admin=True)
    repo = AsyncMock()
    repo.create.side_effect = make_article
    object_storage = AsyncMock()
    use_case = CreateArticle(
        repo=repo,
        user=user,
        object_storage=object_storage,
    )
    article_data = ArticleData(
        title="First article",
        content="Some interesting content",
        category_id=1,
        image_object_key=None,
    )

    await use_case.execute(article_data)

    object_storage.upload_file.assert_not_called()
    saved_article_data = repo.create.await_args.args[0]
    assert saved_article_data.image_object_key is None


@pytest.mark.asyncio
async def test_update_article_uploads_image_and_updates_object_key(
    user_factory,
) -> None:
    user = user_factory(is_admin=True)
    article_id = uuid4()
    repo = AsyncMock()
    object_storage = AsyncMock()
    object_storage.upload_file.return_value = StoredObject(
        object_key="articles/images/20260731/new-image.webp"
    )
    repo.update.side_effect = lambda _, data: make_article(
        ArticleData(
            title=data.title or "First article",
            content=data.content or "Some interesting content",
            category_id=data.category_id,
            image_object_key=data.image_object_key,
        )
    )
    use_case = UpdateArticle(
        repo=repo,
        user=user,
        object_storage=object_storage,
    )
    update_data = ArticleUpdateData(title="Updated article")
    image = FileToUpload(
        filename="image.webp",
        content_type="image/webp",
        file=BytesIO(b"content"),
    )

    article = await use_case.execute(article_id, update_data, image=image)

    object_storage.upload_file.assert_awaited_once_with(image)
    saved_update_data = repo.update.await_args.args[1]
    assert saved_update_data.title == "Updated article"
    assert saved_update_data.image_object_key == "articles/images/20260731/new-image.webp"
    assert article.data.image_object_key == "articles/images/20260731/new-image.webp"


@pytest.mark.asyncio
async def test_update_article_without_image_does_not_touch_image_key(
    user_factory,
) -> None:
    user = user_factory(is_admin=True)
    repo = AsyncMock()
    object_storage = AsyncMock()
    use_case = UpdateArticle(
        repo=repo,
        user=user,
        object_storage=object_storage,
    )
    update_data = ArticleUpdateData(content="Updated article content")

    await use_case.execute(uuid4(), update_data)

    object_storage.upload_file.assert_not_called()
    saved_update_data = repo.update.await_args.args[1]
    assert saved_update_data.content == "Updated article content"
    assert saved_update_data.image_object_key is None
