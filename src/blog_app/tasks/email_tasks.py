from smtplib import SMTPException

from blog_app.core.config import settings
from blog_app.infrastructure.services.notifications import SMTPEmailSender
from blog_app.tasks.celery_app import celery_app


@celery_app.task(
    name="blog_app.send_successful_registration_email",
    autoretry_for=(SMTPException, OSError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def send_successful_registration_email(
    recipient_email: str,
    username: str,
) -> None:
    email_sender = SMTPEmailSender(settings)
    email_sender.send_successful_registration_email(
        recipient_email=recipient_email,
        username=username,
    )
