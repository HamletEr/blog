from datetime import UTC
from io import BytesIO
import re
from types import SimpleNamespace
from unittest.mock import Mock

from botocore.exceptions import BotoCoreError
import pytest

from blog_app.domain.entities.files import FileToUpload
from blog_app.domain.exceptions.object_storage import (
    ObjectDeleteError,
    ObjectUploadError,
    UnsupportedFileTypeError,
    UploadedFileTooLargeError,
)
from blog_app.infrastructure.services.object_storage import S3ObjectStorage


def make_settings(**kwargs):
    defaults = {
        "s3_bucket": "blog-media",
        "s3_public_url": "http://localhost:9000/",
        "s3_article_images_prefix": "articles/images",
        "s3_article_image_max_size_bytes": 10,
        "zone_info": UTC,
        "s3_endpoint_url": "http://localhost:9000",
        "s3_region": "ru-central1",
        "s3_access_key": "access-key",
        "s3_secret_key": "secret-key",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


@pytest.mark.asyncio
async def test_s3_object_storage_uploads_file() -> None:
    client = Mock()
    storage = S3ObjectStorage(make_settings(), client=client)
    file_data = FileToUpload(
        filename="image.png",
        content_type="image/png",
        file=BytesIO(b"content"),
    )

    stored_object = await storage.upload_file(file_data)

    assert re.fullmatch(
        r"articles/images/\d{8}/[0-9a-f-]{36}\.png",
        stored_object.object_key,
    )
    client.upload_fileobj.assert_called_once_with(
        Fileobj=file_data.file,
        Bucket="blog-media",
        Key=stored_object.object_key,
        ExtraArgs={"ContentType": "image/png"},
    )


def test_s3_object_storage_builds_public_url() -> None:
    storage = S3ObjectStorage(make_settings(), client=Mock())

    public_url = storage.get_public_url("/articles/images/image.png")

    assert public_url == "http://localhost:9000/blog-media/articles/images/image.png"


@pytest.mark.asyncio
async def test_s3_object_storage_rejects_unsupported_file_type() -> None:
    storage = S3ObjectStorage(make_settings(), client=Mock())
    file_data = FileToUpload(
        filename="image.gif",
        content_type="image/gif",
        file=BytesIO(b"content"),
    )

    with pytest.raises(UnsupportedFileTypeError):
        await storage.upload_file(file_data)


@pytest.mark.asyncio
async def test_s3_object_storage_rejects_too_large_file() -> None:
    storage = S3ObjectStorage(
        make_settings(s3_article_image_max_size_bytes=3),
        client=Mock(),
    )
    file_data = FileToUpload(
        filename="image.webp",
        content_type="image/webp",
        file=BytesIO(b"content"),
    )

    with pytest.raises(UploadedFileTooLargeError):
        await storage.upload_file(file_data)


@pytest.mark.asyncio
async def test_s3_object_storage_wraps_client_errors() -> None:
    client = Mock()
    client.upload_fileobj.side_effect = BotoCoreError(error_msg="upload failed")
    storage = S3ObjectStorage(make_settings(), client=client)
    file_data = FileToUpload(
        filename="image.jpg",
        content_type="image/jpeg",
        file=BytesIO(b"content"),
    )

    with pytest.raises(ObjectUploadError):
        await storage.upload_file(file_data)


@pytest.mark.asyncio
async def test_s3_object_storage_deletes_file() -> None:
    client = Mock()
    storage = S3ObjectStorage(make_settings(), client=client)

    await storage.delete_file("articles/images/20260731/image.png")

    client.delete_object.assert_called_once_with(
        Bucket="blog-media",
        Key="articles/images/20260731/image.png",
    )


@pytest.mark.asyncio
async def test_s3_object_storage_wraps_delete_errors() -> None:
    client = Mock()
    client.delete_object.side_effect = BotoCoreError(error_msg="delete failed")
    storage = S3ObjectStorage(make_settings(), client=client)

    with pytest.raises(ObjectDeleteError):
        await storage.delete_file("articles/images/20260731/image.png")
