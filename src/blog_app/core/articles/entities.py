from dataclasses import dataclass


@dataclass
class Article:
    id: int
    title: str
    text: str
    category: int
    image_url: str
    is_active: bool
