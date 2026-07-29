from abc import ABC, abstractmethod

from blog_app.domain.entities.users import User


class UserRegistrationNotifier(ABC):
    @abstractmethod
    def send_successful_registration_email(self, user: User) -> None: ...


class EmailSender(ABC):
    @abstractmethod
    def send_successful_registration_email(
        self, recipient_email: str, username: str
    ) -> None: ...
