class UserError(Exception):
    pass


class AuthenticationRequired(UserError):
    pass


class UserNotFound(UserError):
    pass


class UserAlreadyExists(UserError):
    pass
