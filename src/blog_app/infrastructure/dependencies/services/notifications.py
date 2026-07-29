from typing import Annotated

from fastapi import Depends

from blog_app.domain.services.notifications import UserRegistrationNotifier
from blog_app.infrastructure.services.notifications import (
    CeleryUserRegistrationNotifier,
)


def get_user_registration_notifier() -> UserRegistrationNotifier:
    return CeleryUserRegistrationNotifier()


UserRegistrationNotifierDep = Annotated[
    UserRegistrationNotifier,
    Depends(get_user_registration_notifier),
]
