from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ArticleData:
    title: str
    content: str
    category_id: int | None
    image_object_key: str | None


@dataclass
class ArticleUpdateData:
    title: str | None = None
    content: str | None = None
    category_id: int | None = None
    image_object_key: str | None = None
    clear_category: bool = False
    clear_image: bool = False


@dataclass
class Article:
    id: UUID
    is_active: bool
    data: ArticleData
    created_at: datetime
    updated_at: datetime


@dataclass
class ArticlePage:
    items: list[Article]
    total: int
    page: int
    page_size: int
