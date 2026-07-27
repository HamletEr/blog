from fastapi import Response

from blog_app.domain.entities.tokens import TokenPair

ACCESS_TOKEN_COOKIE_KEY = "access_token"
REFRESH_TOKEN_COOKIE_KEY = "refresh_token"


def set_auth_cookies(
    response: Response,
    token_pair: TokenPair,
    *,
    access_max_age: int,
    refresh_max_age: int,
    secure: bool,
) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_KEY,
        value=token_pair.access_token,
        max_age=access_max_age,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_KEY,
        value=token_pair.refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )


def clear_auth_cookies(response: Response, *, secure: bool) -> None:
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE_KEY,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE_KEY,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )


r = Response()


print(r)

r.set_cookie(
    key=ACCESS_TOKEN_COOKIE_KEY,
    value="secret",
    httponly=True,
    samesite="lax",
    secure=True,
    path="/",
)
