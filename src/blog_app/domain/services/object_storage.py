from abc import ABC, abstractmethod

from blog_app.domain.entities.files import FileToUpload, StoredObject


class ObjectStorage(ABC):
    @abstractmethod
    async def upload_file(self, file: FileToUpload) -> StoredObject:
        raise NotImplementedError

    @abstractmethod
    async def delete_file(self, object_key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_public_url(self, object_key: str) -> str:
        raise NotImplementedError
