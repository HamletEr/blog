from celery import Celery

from blog_app.core.config import settings

celery_app = Celery(
    "blog_app",
    broker=settings.celery_broker_url,
    include=["blog_app.tasks.email_tasks"],
)

celery_app.conf.task_default_queue = settings.rabbitmq_queue
celery_app.conf.task_ignore_result = True
