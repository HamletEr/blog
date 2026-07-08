class ArticleError(Exception):
    pass


class ArticleNotFoundError(ArticleError):
    pass


class PermissionDenied(ArticleError):
    pass


class TooShortText(ArticleError):
    pass
