from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from blog_app.domain.exceptions.articles import (
    ArticleNotFoundError,
    IncorrectLimitOnPage,
    IncorrectPageNumber,
    PermissionDenied as ArticlePermissionDenied,
    TooShortText,
)
from blog_app.domain.exceptions.categories import (
    CategoryAlreadyExists,
    CategoryNotFound,
)
from blog_app.domain.exceptions.object_storage import (
    ObjectUploadError,
    UnsupportedFileTypeError,
    UploadedFileTooLargeError,
)
from blog_app.domain.exceptions.tokens import ExpiredToken, InvalidToken
from blog_app.domain.exceptions.users import (
    AuthenticationRequired,
    EmailAlreadyExists,
    IncorrectPassword,
    PermissionDenied as UserPermissionDenied,
    TooEasyPassword,
    UserAlreadyExists,
    UserEmailRequired,
    UserIdOrUserEmailRequired,
    UserIdRequired,
    UserNotFound,
)


def _json_error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthenticationRequired)
    async def handle_authentication_required(
        request: Request, exc: AuthenticationRequired
    ) -> JSONResponse:
        return _json_error(status.HTTP_401_UNAUTHORIZED, "Authentication required")

    @app.exception_handler(InvalidToken)
    async def handle_invalid_token(request: Request, exc: InvalidToken) -> JSONResponse:
        return _json_error(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    @app.exception_handler(ExpiredToken)
    async def handle_expired_token(request: Request, exc: ExpiredToken) -> JSONResponse:
        return _json_error(status.HTTP_401_UNAUTHORIZED, "Token expired")

    @app.exception_handler(UserPermissionDenied)
    async def handle_user_permission_denied(
        request: Request, exc: UserPermissionDenied
    ) -> JSONResponse:
        return _json_error(status.HTTP_403_FORBIDDEN, "Permission denied")

    @app.exception_handler(ArticlePermissionDenied)
    async def handle_article_permission_denied(
        request: Request, exc: ArticlePermissionDenied
    ) -> JSONResponse:
        return _json_error(status.HTTP_403_FORBIDDEN, "Permission denied")

    @app.exception_handler(UserNotFound)
    async def handle_user_not_found(
        request: Request, exc: UserNotFound
    ) -> JSONResponse:
        return _json_error(status.HTTP_404_NOT_FOUND, "User not found")

    @app.exception_handler(ArticleNotFoundError)
    async def handle_article_not_found(
        request: Request, exc: ArticleNotFoundError
    ) -> JSONResponse:
        return _json_error(status.HTTP_404_NOT_FOUND, "Article not found")

    @app.exception_handler(UserAlreadyExists)
    async def handle_user_already_exists(
        request: Request, exc: UserAlreadyExists
    ) -> JSONResponse:
        detail = str(exc) or "User already exists"
        return _json_error(status.HTTP_409_CONFLICT, detail)

    @app.exception_handler(EmailAlreadyExists)
    async def handle_email_already_exists(
        request: Request, exc: EmailAlreadyExists
    ) -> JSONResponse:
        detail = str(exc) or "Email already exists"
        return _json_error(status.HTTP_409_CONFLICT, detail)

    @app.exception_handler(IncorrectPassword)
    async def handle_incorrect_password(
        request: Request, exc: IncorrectPassword
    ) -> JSONResponse:
        return _json_error(status.HTTP_401_UNAUTHORIZED, "Incorrect password")

    @app.exception_handler(TooEasyPassword)
    async def handle_too_easy_password(
        request: Request, exc: TooEasyPassword
    ) -> JSONResponse:
        detail = str(exc) or "Password is too easy"
        return _json_error(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)

    @app.exception_handler(TooShortText)
    async def handle_too_short_text(
        request: Request, exc: TooShortText
    ) -> JSONResponse:
        detail = str(exc) or "Text is too short"
        return _json_error(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)

    @app.exception_handler(IncorrectLimitOnPage)
    async def handle_incorrect_limit_on_page(
        request: Request, exc: IncorrectLimitOnPage
    ) -> JSONResponse:
        detail = str(exc) or "Incorrect limit on page"
        return _json_error(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)

    @app.exception_handler(IncorrectPageNumber)
    async def handle_incorrect_page_number(
        request: Request, exc: IncorrectPageNumber
    ) -> JSONResponse:
        detail = str(exc) or "Incorrect page number"
        return _json_error(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)

    @app.exception_handler(UserIdRequired)
    async def handle_user_id_required(
        request: Request, exc: UserIdRequired
    ) -> JSONResponse:
        return _json_error(status.HTTP_400_BAD_REQUEST, "User id is required")

    @app.exception_handler(UserEmailRequired)
    async def handle_user_email_required(
        request: Request, exc: UserEmailRequired
    ) -> JSONResponse:
        return _json_error(status.HTTP_400_BAD_REQUEST, "User email is required")

    @app.exception_handler(UserIdOrUserEmailRequired)
    async def handle_user_id_or_email_required(
        request: Request, exc: UserIdOrUserEmailRequired
    ) -> JSONResponse:
        return _json_error(
            status.HTTP_400_BAD_REQUEST,
            "User id or user email is required",
        )

    @app.exception_handler(CategoryAlreadyExists)
    async def handle_category_already_exists(
        request: Request, exc: CategoryAlreadyExists
    ) -> JSONResponse:
        return _json_error(status.HTTP_409_CONFLICT, "Category already exists")

    @app.exception_handler(CategoryNotFound)
    async def handle_category_not_found(
        request: Request, exc: CategoryNotFound
    ) -> JSONResponse:
        return _json_error(status.HTTP_404_NOT_FOUND, "Category not found")

    @app.exception_handler(UnsupportedFileTypeError)
    async def handle_unsupported_file_type(
        request: Request, exc: UnsupportedFileTypeError
    ) -> JSONResponse:
        detail = str(exc) or "Unsupported file type"
        return _json_error(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)

    @app.exception_handler(UploadedFileTooLargeError)
    async def handle_uploaded_file_too_large(
        request: Request, exc: UploadedFileTooLargeError
    ) -> JSONResponse:
        detail = str(exc) or "Uploaded file is too large"
        return _json_error(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)

    @app.exception_handler(ObjectUploadError)
    async def handle_object_upload_error(
        request: Request, exc: ObjectUploadError
    ) -> JSONResponse:
        return _json_error(status.HTTP_502_BAD_GATEWAY, "Object storage is unavailable")
