from typing import Annotated

from fastapi import Depends

from blog_app.core.config import settings
from blog_app.domain.services.object_storage import ObjectStorage
from blog_app.infrastructure.services.object_storage import S3ObjectStorage

_object_storage: ObjectStorage | None = None


def get_object_storage() -> ObjectStorage:
    global _object_storage

    if _object_storage is None:
        _object_storage = S3ObjectStorage(settings)

    return _object_storage


ObjectStorageDep = Annotated[ObjectStorage, Depends(get_object_storage)]
