from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from blog_app.domain.entities.users import User
from blog_app.domain.exceptions.users import (
    EmailAlreadyExists,
    UserAlreadyExists,
    UserIdOrUserEmailRequired,
    UserIdRequired,
    UserNotFound,
)
from blog_app.domain.repositories.users import UserRepository
from blog_app.infrastructure.models.users import UserModel


class PGUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _model_to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            hashed_password=model.hashed_password,
            is_active=model.is_active,
            is_admin=model.is_admin,
            registered_at=model.registered_at,
        )

    async def get(
        self, user_id: UUID | None = None, user_email: str | None = None
    ) -> User | None:
        if not user_id and not user_email:
            raise UserIdOrUserEmailRequired()
        if user_id:
            stmt = select(UserModel).where(UserModel.id == user_id)
        else:
            stmt = select(UserModel).where(UserModel.email == user_email)
        user: UserModel | None = (
            await self._session.execute(stmt)
        ).scalar_one_or_none()
        return self._model_to_domain(user) if user else None

    async def create(self, user: User) -> User:
        user_model = UserModel(
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            is_admin=user.is_admin,
        )
        self._session.add(user_model)
        try:
            await self._session.flush()
        except IntegrityError as err:
            if "uq_users_email" in str(err.orig):
                raise UserAlreadyExists(
                    f"User with {user.email} already exists."
                ) from err
            raise
        return self._model_to_domain(user_model)

    async def update(self, user: User) -> User:
        if not user.id:
            raise UserIdRequired()
        stmt = select(UserModel).where(UserModel.id == user.id)
        user_in_db: UserModel | None = (
            await self._session.execute(stmt)
        ).scalar_one_or_none()
        if not user_in_db:
            raise UserNotFound()

        user_in_db.username = user.username
        user_in_db.email = user.email
        user_in_db.hashed_password = user.hashed_password
        user_in_db.is_active = user.is_active
        user_in_db.is_admin = user.is_admin

        try:
            await self._session.flush()
        except IntegrityError as err:
            if "uq_users_email" in str(err.orig):
                raise EmailAlreadyExists(
                    f"User with {user.email} already exists."
                ) from err
            raise
        return self._model_to_domain(user_in_db)
