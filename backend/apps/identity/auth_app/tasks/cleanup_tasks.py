"""
Celery task: nightly cleanup of expired auth records.
Scheduled task to purge expired OTPRecord and PasswordResetToken rows.
"""

import logging
from celery import shared_task
from django.utils.timezone import now

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_auth_records():
    """
    Delete expired OTPRecord and unused-but-expired PasswordResetToken rows.
    Scheduled nightly at 3 AM via CELERYBEAT_SCHEDULE.
    """
    from apps.identity.auth_app.models import OTPRecord, PasswordResetToken

    deleted_otps, _ = OTPRecord.objects.filter(expires_at__lt=now()).delete()
    deleted_tokens, _ = PasswordResetToken.objects.filter(
        expires_at__lt=now(), used=False
    ).delete()

    logger.info(
        "Auth cleanup: deleted_otps=%d, deleted_tokens=%d",
        deleted_otps, deleted_tokens,
    )
    return {"deleted_otps": deleted_otps, "deleted_tokens": deleted_tokens}
