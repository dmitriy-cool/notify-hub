from app.tasks.celery_app import app  # noqa: F401

# Explicitly import tasks to register them with Celery
from app.tasks.email import send_email  # noqa: F401

__all__ = ['app']
