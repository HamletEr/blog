from types import SimpleNamespace
from unittest.mock import Mock, patch

from blog_app.infrastructure.services.notifications import (
    CeleryUserRegistrationNotifier,
    SMTPEmailSender,
)


def test_celery_registration_notifier_enqueues_task(user_factory) -> None:
    user = user_factory()

    with patch(
        "blog_app.tasks.email_tasks."
        "send_successful_registration_email"
    ) as task:
        notifier = CeleryUserRegistrationNotifier()

        notifier.send_successful_registration_email(user)

    task.delay.assert_called_once_with(
        recipient_email=user.email,
        username=user.username,
    )


def test_smtp_email_sender_builds_and_sends_message() -> None:
    smtp_client = Mock()
    settings = SimpleNamespace(
        smtp_host="localhost",
        smtp_port=1025,
        smtp_user="",
        smtp_password="",
        smtp_from_email="no-reply@blog.local",
        smtp_from_name="Blog App",
        smtp_use_tls=False,
    )

    with patch(
        "blog_app.infrastructure.services.notifications.SMTP"
    ) as smtp_constructor:
        smtp_constructor.return_value.__enter__.return_value = smtp_client
        email_sender = SMTPEmailSender(settings)

        email_sender.send_successful_registration_email(
            recipient_email="alice@example.com",
            username="alice",
        )

    smtp_client.send_message.assert_called_once()
    message = smtp_client.send_message.call_args.args[0]
    assert message["To"] == "alice@example.com"
    assert message["Subject"] == "Successful registration"
    assert "alice" in message.get_content()
