from dataclasses import dataclass

from blog_app.domain.entities.users import User


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass(frozen=True)
class AuthResult:
    user: User
    tokens: TokenPair
