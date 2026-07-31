from datetime import datetime
from typing import Annotated, Any

from pydantic import (
    UUID4,
    AliasChoices,
    AnyUrl,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PositiveInt,
)


def strip_string(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


Title = Annotated[
    str, Field(min_length=2, max_length=100), BeforeValidator(strip_string)
]

Content = Annotated[str, Field(min_length=2, max_length=1_000_000)]


class ArticleDataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: Title
    content: Content
    category_id: PositiveInt | None
    image_url: AnyUrl | None = Field(
        validation_alias=AliasChoices("image_url", "image_object_key")
    )


class ArticleViewSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    data: ArticleDataSchema
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    detail: str
