class TokenError(Exception):
    pass


class InvalidToken(TokenError):
    pass


class ExpiredToken(TokenError):
    pass
