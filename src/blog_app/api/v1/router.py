from fastapi import APIRouter

from blog_app.api.v1.routes import health, users

main_router = APIRouter(
    prefix="/api/v1",
)

main_router.include_router(health.router, tags=["health"])
main_router.include_router(users.router, tags=["users"])
