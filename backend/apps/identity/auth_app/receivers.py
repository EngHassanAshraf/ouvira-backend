"""
Signal receiver for password_changed.

IP extraction uses django-ipware at the VIEW level before
dispatching the Celery task. The signal receiver here only forwards
the already-extracted primitives into the task queue.

The signal is ALWAYS fired via transaction.on_commit() — never inside
an atomic block.
"""

import logging
from django.utils.timezone import now

from apps.identity.auth_app.signals import password_changed

logger = logging.getLogger(__name__)


def handle_password_changed(sender, user, ip: str, user_agent: str, **kwargs):
    """
    Connected to the password_changed signal.
    Enqueues send_password_changed_email with JSON-serializable primitives only.
    No Django model instances passed to Celery.
    """
    try:
        from apps.identity.auth_app.tasks.send_password_changed_email import send_password_changed_email
        send_password_changed_email.delay(
            user_id=user.id,
            ip=ip,
            user_agent=user_agent,
            timestamp=now().isoformat(),
        )
    except Exception:
        logger.exception(
            "Failed to enqueue password-changed email | user_id=%s", user.id
        )


# Connect the receiver
password_changed.connect(handle_password_changed)
