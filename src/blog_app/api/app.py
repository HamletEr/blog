from fastapi import FastAPI

from blog_app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.app_name} ({settings.app_env})",
        version=settings.app_version,
        debug=settings.debug,
        redoc_url=None,
    )
    return app
