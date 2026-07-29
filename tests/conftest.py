from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from blog_app.domain.entities.users import User


@pytest.fixture
def settings_stub() -> SimpleNamespace:
    return SimpleNamespace(
        app_name="blog-app",
        jwt_algorithm="HS256",
        jwt_access_secret="access-secret-access-secret-1234",
        jwt_access_ttl_minutes=15,
        jwt_refresh_secret="refresh-secret-refresh-secret-1234",
        jwt_refresh_ttl_minutes=60,
    )


@pytest.fixture
def user_factory() -> Any:
    def make_user(**kwargs: Any) -> User:
        return User(
            id=kwargs.pop("id", uuid4()),
            username=kwargs.pop("username", "alice"),
            email=kwargs.pop("email", "alice@example.com"),
            hashed_password=kwargs.pop("hashed_password", "hashed-secret"),
            is_active=kwargs.pop("is_active", True),
            is_admin=kwargs.pop("is_admin", False),
            registered_at=kwargs.pop("registered_at", datetime.now(UTC)),
        )

    return make_user
