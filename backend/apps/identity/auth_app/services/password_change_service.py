"""
Password Change Service — handles authenticated password change.

Security properties:
- is_password_reused() iterates PasswordHistory rows explicitly.
- history tracked in PasswordHistory (up to 5 checked, unlimited stored).
- password_changed signal fired after successful change.
"""

import logging

from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.identity.auth_app.models import PasswordHistory
from apps.identity.auth_app.signals import password_changed
from apps.identity.auth_app.utils.password_utils import is_password_reused
from apps.identity.auth_app.utils import validate_user_password
from apps.shared.exceptions import BusinessException

logger = logging.getLogger(__name__)


class PasswordChangeService:

    @staticmethod
    def change_password(
        user,
        old_password: str,
        new_password: str,
        ip: str,
        user_agent: str,
    ) -> None:
        """
        Authenticated password change.

        1. Verify old_password against stored bcrypt hash.
        2. Validate new_password policy.
        3. Check PasswordHistory (last 5 rows) for reuse.
        4. Hash and save new password.
        5. Append to PasswordHistory.
        6. Fire password_changed signal via on_commit.

        Raises ValidationError or BusinessException on failure.
        """
        # Step 1: Verify old password
        if not user.check_password(old_password):
            raise BusinessException("wrong_password")

        # Step 2: Policy check
        validate_user_password(new_password)

        # Step 3: Email Verification Check
        if not user.email_verified:
            raise ValidationError({
                "error": "email_not_verified",
                "detail": "Email not verified.",
            })

        # Step 4: History reuse check
        if is_password_reused(user, new_password):
            raise ValidationError({
                "error": "password_reused",
                "detail": "Cannot reuse a recent password.",
            })

        with transaction.atomic():
            # CRYPTO-003: Reject passwords > 72 UTF-8 bytes (bcrypt silent truncation guard)
            if len(new_password.encode("utf-8")) > 72:
                raise ValidationError({"error": "password_too_long", "detail": "Password must not exceed 72 bytes."})
            user.password = make_password(new_password)
            user.save(update_fields=["password"])

            PasswordHistory.objects.create(
                user=user,
                password_hash=user.password,
                changed_via="change",
            )

            transaction.on_commit(lambda: password_changed.send(
                sender=user.__class__,
                user=user,
                ip=ip,
                user_agent=user_agent,
            ))

        logger.info("Password changed | user_id=%s | ip=<redacted>", user.pk)
