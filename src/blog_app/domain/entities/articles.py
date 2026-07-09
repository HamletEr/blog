from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ArticleData:
    title: str
    content: str
    category_id: int | None
    image_url: str | None


@dataclass
class Article:
    id: UUID
    is_active: bool
    data: ArticleData
    created_at: datetime
    updated_at: datetime
