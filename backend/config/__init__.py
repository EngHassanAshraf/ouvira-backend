# Expose the Celery application instance for `celery -A config` discovery
from .celery import app as celery_app

__all__ = ("celery_app",)
