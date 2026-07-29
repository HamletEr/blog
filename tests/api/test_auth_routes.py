from unittest.mock import AsyncMock

import pytest

from blog_app.api.auth_cookies import ACCESS_TOKEN_COOKIE_KEY, REFRESH_TOKEN_COOKIE_KEY
from blog_app.domain.entities.tokens import AuthResult, TokenPair
from blog_app.domain.exceptions.tokens import InvalidToken
from blog_app.domain.exceptions.users import PermissionDenied, UserNotFound
from blog_app.infrastructure.dependencies.use_cases import (
    get_login_and_issue_tokens_use_case,
    get_refresh_token_pair_use_case,
    get_revoke_refresh_token_use_case,
)


def test_login_returns_user_and_sets_auth_cookies(app, client, user_factory) -> None:
    user = user_factory()
    use_case = AsyncMock()
    use_case.execute.return_value = AuthResult(
        user=user,
        tokens=TokenPair(
            access_token="access-token",
            refresh_token="refresh-token",
        ),
    )
    app.dependency_overrides[get_login_and_issue_tokens_use_case] = lambda: use_case

    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "StrongPass123"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"] == str(user.id)
    assert client.cookies.get(ACCESS_TOKEN_COOKIE_KEY) == "access-token"
    assert client.cookies.get(REFRESH_TOKEN_COOKIE_KEY) == "refresh-token"


def test_login_returns_401_for_invalid_credentials(app, client) -> None:
    use_case = AsyncMock()
    use_case.execute.side_effect = UserNotFound()
    app.dependency_overrides[get_login_and_issue_tokens_use_case] = lambda: use_case

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_refresh_returns_401_when_refresh_cookie_is_missing(client) -> None:
    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert response.json() == {"detail": "Refresh token is missing"}


def test_refresh_rotates_cookies(app, client) -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = TokenPair(
        access_token="new-access-token",
        refresh_token="new-refresh-token",
    )
    app.dependency_overrides[get_refresh_token_pair_use_case] = lambda: use_case
    client.cookies.set(
        REFRESH_TOKEN_COOKIE_KEY,
        "old-refresh-token",
        domain="testserver.local",
        path="/",
    )

    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 200
    assert response.json() == {"detail": "Session refreshed"}
    assert client.cookies.get(ACCESS_TOKEN_COOKIE_KEY) == "new-access-token"
    assert (
        client.cookies.get(
            REFRESH_TOKEN_COOKIE_KEY,
            domain="testserver.local",
            path="/",
        )
        == "new-refresh-token"
    )
    use_case.execute.assert_awaited_once_with("old-refresh-token")


@pytest.mark.parametrize(
    "error",
    [InvalidToken(), PermissionDenied(), UserNotFound()],
)
def test_refresh_returns_401_and_clears_cookies_on_invalid_token(
    app,
    client,
    error,
) -> None:
    use_case = AsyncMock()
    use_case.execute.side_effect = error
    app.dependency_overrides[get_refresh_token_pair_use_case] = lambda: use_case
    client.cookies.set(
        ACCESS_TOKEN_COOKIE_KEY,
        "old-access-token",
        domain="testserver.local",
        path="/",
    )
    client.cookies.set(
        REFRESH_TOKEN_COOKIE_KEY,
        "old-refresh-token",
        domain="testserver.local",
        path="/",
    )

    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid refresh token"}
    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any(
        f"{ACCESS_TOKEN_COOKIE_KEY}=" in header for header in set_cookie_headers
    )
    assert any(
        f"{REFRESH_TOKEN_COOKIE_KEY}=" in header for header in set_cookie_headers
    )


def test_logout_returns_204_and_clears_cookies(app, client) -> None:
    use_case = AsyncMock()
    app.dependency_overrides[get_revoke_refresh_token_use_case] = lambda: use_case
    client.cookies.set(ACCESS_TOKEN_COOKIE_KEY, "access-token")
    client.cookies.set(REFRESH_TOKEN_COOKIE_KEY, "refresh-token")

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 204
    use_case.execute.assert_awaited_once_with("refresh-token")
    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any(f"{ACCESS_TOKEN_COOKIE_KEY}=" in header for header in set_cookie_headers)
    assert any(
        f"{REFRESH_TOKEN_COOKIE_KEY}=" in header for header in set_cookie_headers
    )


def test_logout_ignores_invalid_refresh_token(app, client) -> None:
    use_case = AsyncMock()
    use_case.execute.side_effect = InvalidToken()
    app.dependency_overrides[get_revoke_refresh_token_use_case] = lambda: use_case
    client.cookies.set(REFRESH_TOKEN_COOKIE_KEY, "broken-refresh-token")

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 204
