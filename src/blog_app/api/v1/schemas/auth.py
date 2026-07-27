from pydantic import BaseModel

from blog_app.api.v1.schemas.users import UserInfo


class AuthResponse(BaseModel):
    user: UserInfo


class MessageResponse(BaseModel):
    detail: str
