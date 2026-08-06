from email.message import EmailMessage
from smtplib import SMTP

from celery.exceptions import CeleryError
from kombu.exceptions import KombuError, OperationalError

from blog_app.core.config import Settings
from blog_app.domain.entities.users import User
from blog_app.domain.exceptions.notifications import NotificationDeliveryError
from blog_app.domain.services.notifications import EmailSender, UserRegistrationNotifier


class CeleryUserRegistrationNotifier(UserRegistrationNotifier):
    def send_successful_registration_email(self, user: User) -> None:
        from blog_app.tasks.email_tasks import send_successful_registration_email

        try:
            send_successful_registration_email.delay(
                recipient_email=user.email,
                username=user.username,
            )
        except (CeleryError, KombuError, OperationalError) as err:
            raise NotificationDeliveryError from err


class SMTPEmailSender(EmailSender):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send_successful_registration_email(
        self, recipient_email: str, username: str
    ) -> None:
        message = self._build_successful_registration_message(
            recipient_email=recipient_email,
            username=username,
        )
        self._send_message(message)

    def _build_successful_registration_message(
        self, recipient_email: str, username: str
    ) -> EmailMessage:
        message = EmailMessage()
        sender_name = self.settings.smtp_from_name
        sender_email = self.settings.smtp_from_email
        if sender_name:
            message["From"] = f"{sender_name} <{sender_email}>"
        else:
            message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = "Successful registration"
        message.set_content(
            f"Hello, {username}!\n\n"
            "Your registration was completed successfully.\n"
            "You can now sign in and start using the blog.\n"
        )
        return message

    def _send_message(self, message: EmailMessage) -> None:
        with SMTP(host=self.settings.smtp_host, port=self.settings.smtp_port) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_user:
                smtp.login(self.settings.smtp_user, self.settings.smtp_password)
            smtp.send_message(message)
