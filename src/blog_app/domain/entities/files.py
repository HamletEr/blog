from dataclasses import dataclass
from typing import BinaryIO


@dataclass(frozen=True)
class FileToUpload:
    filename: str
    content_type: str
    file: BinaryIO


@dataclass(frozen=True)
class StoredObject:
    object_key: str
