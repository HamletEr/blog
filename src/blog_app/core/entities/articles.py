from dataclasses import dataclass


@dataclass
class ArticleData:
    title: str
    content: str
    category: int | None
    image_url: str | None


@dataclass
class Article:
    id: int
    is_active: bool
    data: ArticleData
