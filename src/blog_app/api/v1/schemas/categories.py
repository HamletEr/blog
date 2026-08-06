from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def strip_string(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


CategoryNameField = Annotated[
    str, Field(min_length=2, max_length=50), BeforeValidator(strip_string)
]


class CategoryInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CategoryName(BaseModel):
    value: CategoryNameField
