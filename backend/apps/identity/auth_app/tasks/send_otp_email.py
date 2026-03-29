"""
Celery task: send OTP via email.
"""
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


# @shared_task(bind=True, max_retries=3)
def send_otp_email(self, email: str, raw_otp: str):
    """Send OTP to email address. Accepts only primitives."""
    try:
        send_mail(
            subject="Your Ouvira verification code",
            message=(
                f"Your Ouvira OTP is: {raw_otp}\n\n"
                f"This code expires in 10 minutes.\n"
                f"If you did not request this, please ignore this email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info("OTP email sent | email=<redacted>")
    except Exception as exc:
        logger.exception("Failed to send OTP email | attempt=%s", self.request.retries + 1)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
