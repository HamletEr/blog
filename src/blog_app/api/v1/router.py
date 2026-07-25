from fastapi import APIRouter

from blog_app.api.v1.routes.health import router as health_router
from blog_app.api.v1.routes.users import router as users_router

main_router = APIRouter(
    prefix="/api/v1",
)

main_router.include_router(health_router, tags=["health"])
main_router.include_router(users_router, tags=["users"])
