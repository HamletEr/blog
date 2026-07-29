from unittest.mock import AsyncMock

from blog_app.api.auth_cookies import ACCESS_TOKEN_COOKIE_KEY, REFRESH_TOKEN_COOKIE_KEY
from blog_app.domain.entities.tokens import AuthResult, TokenPair
from blog_app.infrastructure.dependencies.use_cases import (
    get_register_and_issue_tokens_use_case,
)


def test_create_user_returns_auth_response_and_sets_cookies(
    app,
    client,
    user_factory,
) -> None:
    user = user_factory()
    use_case = AsyncMock()
    use_case.execute.return_value = AuthResult(
        user=user,
        tokens=TokenPair(
            access_token="access-token",
            refresh_token="refresh-token",
        ),
    )
    app.dependency_overrides[get_register_and_issue_tokens_use_case] = (
        lambda: use_case
    )

    response = client.post(
        "/api/v1/users/",
        json={
            "username": user.username,
            "email": user.email,
            "password": "StrongPass123",
        },
    )

    assert response.status_code == 201
    assert response.json()["user"]["id"] == str(user.id)
    assert client.cookies.get(ACCESS_TOKEN_COOKIE_KEY) == "access-token"
    assert client.cookies.get(REFRESH_TOKEN_COOKIE_KEY) == "refresh-token"
