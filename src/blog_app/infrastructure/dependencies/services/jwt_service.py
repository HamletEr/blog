from typing import Annotated

from fastapi import Depends

from blog_app.core.config import settings
from blog_app.domain.services.jwt_service import TokenService
from blog_app.infrastructure.services.jwt_service import JWTService


def get_jwt_service() -> TokenService:
    return JWTService(settings)


JWTServiceDep = Annotated[TokenService, Depends(get_jwt_service)]
