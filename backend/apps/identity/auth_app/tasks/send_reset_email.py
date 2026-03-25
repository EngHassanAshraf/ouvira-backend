"""
Celery task: send password reset link via email.
"""
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_reset_email(self, email: str, reset_url: str):
    """Send reset link to email address. Accepts only primitives."""
    try:
        send_mail(
            subject="Reset your Ouvira password",
            message=(
                f"You requested a password reset for your Ouvira account.\n\n"
                f"Click the link below to reset your password (valid for 1 hour):\n"
                f"{reset_url}\n\n"
                f"If you did not request this, please ignore this email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info("Reset email sent | email=<redacted>")
    except Exception as exc:
        logger.exception("Failed to send reset email | attempt=%s", self.request.retries + 1)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
