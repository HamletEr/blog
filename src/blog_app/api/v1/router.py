from fastapi import APIRouter

from blog_app.api.v1.routes.articles import router as articles_router
from blog_app.api.v1.routes.auth import router as auth_router
from blog_app.api.v1.routes.categories import router as categories_router
from blog_app.api.v1.routes.health import router as health_router
from blog_app.api.v1.routes.users import router as users_router

main_router = APIRouter(
    prefix="/api/v1",
)

main_router.include_router(health_router, tags=["health"])
main_router.include_router(auth_router, tags=["auth"])
main_router.include_router(users_router, tags=["users"])
main_router.include_router(categories_router, tags=["categories"])
main_router.include_router(articles_router, tags=["articles"])
