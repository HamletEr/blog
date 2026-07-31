import asyncio
from datetime import datetime
import os
from typing import Any, Protocol
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from blog_app.core.config import Settings
from blog_app.domain.entities.files import FileToUpload, StoredObject
from blog_app.domain.exceptions.object_storage import (
    ObjectDeleteError,
    ObjectUploadError,
    UnsupportedFileTypeError,
    UploadedFileTooLargeError,
)
from blog_app.domain.services.object_storage import ObjectStorage

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class S3Client(Protocol):
    def upload_fileobj(
        self,
        Fileobj: Any,
        Bucket: str,
        Key: str,
        ExtraArgs: dict[str, str],
    ) -> None:
        pass

    def delete_object(self, Bucket: str, Key: str) -> None:
        pass


class S3ObjectStorage(ObjectStorage):
    def __init__(self, settings: Settings, client: S3Client | None = None) -> None:
        self._bucket = settings.s3_bucket
        self._public_url = settings.s3_public_url.rstrip("/")
        self._prefix = settings.s3_article_images_prefix.strip("/")
        self._max_size_bytes = settings.s3_article_image_max_size_bytes
        self._zone_info = settings.zone_info
        self._client = client or boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )

    async def upload_file(self, file: FileToUpload) -> StoredObject:
        extension = self._get_extension(file.content_type)
        self._validate_size(file)

        object_key = self._build_object_key(extension)
        file.file.seek(0)

        try:
            await asyncio.to_thread(
                self._client.upload_fileobj,
                Fileobj=file.file,
                Bucket=self._bucket,
                Key=object_key,
                ExtraArgs={"ContentType": file.content_type},
            )
        except (BotoCoreError, ClientError) as exc:
            raise ObjectUploadError("Failed to upload object to S3") from exc

        return StoredObject(object_key=object_key)

    async def delete_file(self, object_key: str) -> None:
        try:
            await asyncio.to_thread(
                self._client.delete_object,
                Bucket=self._bucket,
                Key=object_key,
            )
        except (BotoCoreError, ClientError) as exc:
            raise ObjectDeleteError("Failed to delete object from S3") from exc

    def get_public_url(self, object_key: str) -> str:
        normalized_key = object_key.lstrip("/")
        return f"{self._public_url}/{self._bucket}/{normalized_key}"

    def _get_extension(self, content_type: str) -> str:
        try:
            return ALLOWED_IMAGE_CONTENT_TYPES[content_type]
        except KeyError as exc:
            raise UnsupportedFileTypeError(
                f"Unsupported file content type: {content_type}"
            ) from exc

    def _validate_size(self, file: FileToUpload) -> None:
        current_position = file.file.tell()
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(current_position)

        if size > self._max_size_bytes:
            raise UploadedFileTooLargeError(
                f"File size must not exceed {self._max_size_bytes} bytes"
            )

    def _build_object_key(self, extension: str) -> str:
        date_part = datetime.now(self._zone_info).strftime("%Y%m%d")
        return f"{self._prefix}/{date_part}/{uuid4()}{extension}"
