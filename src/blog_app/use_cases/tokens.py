from uuid import UUID, uuid4

from blog_app.domain.entities.enums import TokenType
from blog_app.domain.entities.tokens import TokenPair
from blog_app.domain.entities.users import User
from blog_app.domain.exceptions.tokens import InvalidToken
from blog_app.domain.exceptions.users import PermissionDenied, UserNotFound
from blog_app.domain.repositories.tokens import RefreshTokenRepository
from blog_app.domain.repositories.users import UserRepository
from blog_app.domain.services.jwt_service import TokenService


class BaseTokenUseCase:
    def __init__(self, token_service: TokenService) -> None:
        self.token_service = token_service


class IssueTokenPairUseCase(BaseTokenUseCase):
    def __init__(
        self,
        token_service: TokenService,
        refresh_token_repo: RefreshTokenRepository,
    ) -> None:
        super().__init__(token_service)
        self.refresh_token_repo = refresh_token_repo

    async def execute(self, user_id: UUID) -> TokenPair:
        refresh_token_id = uuid4()

        access_token = self.token_service.create_token(
            user_id=user_id,
            token_type=TokenType.ACCESS,
        )
        refresh_token = self.token_service.create_token(
            user_id=user_id,
            token_type=TokenType.REFRESH,
            token_id=refresh_token_id,
        )

        await self.refresh_token_repo.save(
            token_id=refresh_token_id,
            user_id=user_id,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
        )


class RefreshTokenPairUseCase(BaseTokenUseCase):
    def __init__(
        self,
        token_service: TokenService,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
    ) -> None:
        super().__init__(token_service)
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

    async def execute(self, refresh_token: str) -> TokenPair:
        token_payload = self.token_service.decode_token(
            refresh_token,
            TokenType.REFRESH,
        )

        user_id = UUID(token_payload["sub"])
        token_id = UUID(token_payload["jti"])

        token_exists = await self.refresh_token_repo.exists(
            token_id=token_id,
            user_id=user_id,
        )
        if not token_exists:
            raise InvalidToken()

        user = await self.user_repo.get(user_id=user_id)
        if not user:
            raise UserNotFound()
        if not user.is_active:
            raise PermissionDenied()

        await self.refresh_token_repo.revoke(token_id)

        new_refresh_token_id = uuid4()

        access_token = self.token_service.create_token(
            user_id=user_id,
            token_type=TokenType.ACCESS,
        )
        new_refresh_token = self.token_service.create_token(
            user_id=user_id,
            token_type=TokenType.REFRESH,
            token_id=new_refresh_token_id,
        )

        await self.refresh_token_repo.save(
            token_id=new_refresh_token_id,
            user_id=user_id,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )


class RevokeRefreshTokenUseCase(BaseTokenUseCase):
    def __init__(
        self,
        token_service: TokenService,
        refresh_token_repo: RefreshTokenRepository,
    ) -> None:
        super().__init__(token_service)
        self.refresh_token_repo = refresh_token_repo

    async def execute(self, refresh_token: str) -> None:
        token_payload = self.token_service.decode_token(
            refresh_token,
            TokenType.REFRESH,
        )
        token_id = UUID(token_payload["jti"])
        await self.refresh_token_repo.revoke(token_id)


class GetCurrentUserByAccessTokenUseCase(BaseTokenUseCase):
    def __init__(self, token_service: TokenService, user_repo: UserRepository) -> None:
        super().__init__(token_service)
        self.user_repo = user_repo

    async def execute(self, access_token: str) -> User:
        token_payload = self.token_service.decode_token(
            access_token,
            TokenType.ACCESS,
        )
        user_id = UUID(token_payload["sub"])
        user = await self.user_repo.get(user_id=user_id)
        if not user or not user.is_active:
            raise UserNotFound()
        return user
