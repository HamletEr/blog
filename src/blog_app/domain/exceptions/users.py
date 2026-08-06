class UserError(Exception):
    pass


class AuthenticationRequired(UserError):
    pass


class UserNotFound(UserError):
    pass


class UserAlreadyExists(UserError):
    pass


class EmailAlreadyExists(UserError):
    pass


class UserIdRequired(UserError):
    pass


class UserEmailRequired(UserError):
    pass


class PermissionDenied(UserError):
    pass


class IncorrectPassword(UserError):
    pass


class UserIdOrUserEmailRequired(UserError):
    pass


class TooEasyPassword(UserError):
    pass
