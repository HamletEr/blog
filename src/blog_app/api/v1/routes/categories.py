from fastapi import APIRouter
from starlette import status

from blog_app.api.v1.schemas.categories import CategoryInfo, CategoryName
from blog_app.infrastructure.dependencies.use_cases import (
    CreateCategoryUseCaseDep,
    GetByIdCategoryUseCaseDep,
    GetListCategoryUseCaseDep,
)

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.get("/", status_code=status.HTTP_200_OK)
async def categories_list(use_case: GetListCategoryUseCaseDep) -> list[CategoryInfo]:
    categories_domain = await use_case.execute()
    return list(CategoryInfo.model_validate(category) for category in categories_domain)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def categories_create(
    use_case: CreateCategoryUseCaseDep, category_name: CategoryName
) -> CategoryInfo:
    category_domain = await use_case.execute(category_name=category_name.value)
    return CategoryInfo.model_validate(category_domain)


@router.get("/{id}", status_code=status.HTTP_200_OK)
async def get_category_by_id(
    category_id: int, use_case: GetByIdCategoryUseCaseDep
) -> CategoryInfo:
    category_domain = await use_case.execute(category_id)
    return CategoryInfo.model_validate(category_domain)
