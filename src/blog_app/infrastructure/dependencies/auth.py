from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request
from starlette import status

from blog_app.domain.entities.users import User


def get_request_user(request: Request) -> User:
    user = cast(User | None, getattr(request.state, "user", None))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


CurrentUserDep = Annotated[User, Depends(get_request_user)]
