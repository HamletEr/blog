class ArticleError(Exception):
    pass


class ArticleNotFoundError(ArticleError):
    pass


class PermissionDenied(ArticleError):
    pass


class TooShortText(ArticleError):
    pass


class ConflictingArticleUpdate(ArticleError):
    pass


class IncorrectLimitOnPage(ArticleError):
    pass


class IncorrectPageNumber(ArticleError):
    pass
