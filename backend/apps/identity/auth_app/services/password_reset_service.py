"""
Password Reset Service — handles forgot-password, token validation, and password reset.

Security properties (per spec):
- consume_and_reset() wrapped in a single atomic transaction.
- Token marked used BEFORE password write inside the transaction.
- History reuse check via is_password_reused() utility (iterates PasswordHistory rows).
- validate_token() uses a plain queryset — no select_for_update() overhead on GET.
- Partial unique index (enforced in migration) limits one active token per user.
         Invalidation happens BEFORE insertion so the index is never violated.
"""

import hashlib
import logging
import secrets

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.db import transaction
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from apps.identity.auth_app.models import PasswordHistory, PasswordResetToken
from apps.identity.auth_app.signals import password_changed
from apps.identity.auth_app.utils.password_utils import is_password_reused
from apps.identity.auth_app.utils import validate_user_password
from apps.identity.auth_app.services.otp_service import OTPService
from apps.identity.auth_app.services.auth_service import AuthService
from apps.shared.exceptions import BusinessException

logger = logging.getLogger(__name__)

RESET_TOKEN_TTL_HOURS = 1
PW_RESET_RATE_KEY = "pw_reset_rate:{identifier}"
PW_RESET_RATE_LIMIT = 3
PW_RESET_RATE_WINDOW = 3600  # seconds


def _hash_token(raw_token: str) -> str:
    """SHA-256(raw_token) → 64-char hex string."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class PasswordResetService:

    # -------- Step 1: Request reset --------

    @staticmethod
    def request_reset(identifier: str, ip: str, user_agent: str) -> None:
        """
        Initiate a password reset for either an email or phone number.

        Always returns None — caller must respond HTTP 200 regardless of
        whether the account exists (prevents user enumeration).

        Invalidation of old tokens happens BEFORE insertion to satisfy
        the partial unique index (one active token per user).
        """
        # DOS-002: Atomic rate-limit — use cache.add() for init + cache.incr() for subsequent
        rate_key = PW_RESET_RATE_KEY.format(identifier=identifier)
        # cache.add() is atomic and sets only if absent; incr() on existing key is also atomic
        if not cache.add(rate_key, 1, timeout=PW_RESET_RATE_WINDOW):
            try:
                count = cache.incr(rate_key)
            except Exception:
                count = cache.get(rate_key, 1)
            if count > PW_RESET_RATE_LIMIT:
                raise BusinessException(
                    "Too many reset requests. Please wait before trying again."
                )

        # Detect channel (email vs SMS) — same logic as OTPService
        channel = OTPService.detect_channel(identifier)

        # Silent lookup — do not reveal whether account exists
        user = AuthService.get_user_by_identifier(identifier)

        if user:
            raw_token = secrets.token_hex(32)  # 64-char cryptographically random hex
            token_hash = _hash_token(raw_token)
            expires_at = now() + __import__("datetime").timedelta(hours=RESET_TOKEN_TTL_HOURS)

            with transaction.atomic():
                # Invalidate BEFORE inserting — the partial index
                # (user_id WHERE used=FALSE) would reject a second active token.
                PasswordResetToken.objects.filter(user=user, used=False).update(used=True)

                PasswordResetToken.objects.create(
                    user=user,
                    token_hash=token_hash,
                    expires_at=expires_at,
                    used=False,
                )

            # Dispatch delivery outside the transaction — failure here doesn't roll back the token
            PasswordResetService._dispatch_reset_link(channel, identifier, raw_token)

        logger.info("Password reset requested | channel=%s | identifier=<redacted>", channel)

    @staticmethod
    def _dispatch_reset_link(channel: str, identifier: str, raw_token: str) -> None:
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
        if channel == "email":
            try:
                from apps.identity.auth_app.tasks.send_reset_email import send_reset_email
                send_reset_email.delay(identifier, reset_url)
            except Exception:
                logger.exception("Failed to enqueue reset email | identifier=<redacted>")
        else:
            try:
                from apps.shared.services.sms_service import send_sms
                send_sms(message=f"Your Ouvira password reset link: {reset_url}", phone=identifier)
            except Exception:
                logger.exception("Failed to send reset SMS | identifier=<redacted>")

    # -------- Step 2: Validate token (GET pre-flight) --------

    @staticmethod
    def validate_token(raw_token: str) -> PasswordResetToken:
        """
        Stateless pre-flight check only. Token validity is re-confirmed atomically
        inside consume_and_reset(). Do not use select_for_update() here — the lock
        cannot span HTTP requests and provides false protection.

        Raises BusinessException if token is invalid or expired.
        Returns the PasswordResetToken record on success.
        """
        token_hash = _hash_token(raw_token)

        # plain queryset — no select_for_update() overhead here
        record = PasswordResetToken.objects.filter(
            token_hash=token_hash,
            used=False,
            expires_at__gt=now(),
        ).first()

        if not record:
            # Deliberate single error code — do not distinguish expired vs not-found
            raise BusinessException("invalid_or_expired_token")

        return record

    # -------- Step 3: Consume token and reset password --------

    @staticmethod
    def consume_and_reset(
        raw_token: str,
        new_password: str,
        ip: str,
        user_agent: str,
    ) -> None:
        """
        Full atomic transaction with fail-safe token marking order.

        Execution order inside atomic():
          1. Mark THIS token used=True (fail-safe first — see comment below)
          2. Invalidate ALL other active tokens for this user
          3. Set new password
          4. Save user
          5. Append to PasswordHistory

        Signal fired AFTER commit via on_commit() — never inside the transaction.
        """
        token_hash = _hash_token(raw_token)  # QUAL-001: compute hash BEFORE atomic block

        with transaction.atomic():
            # QUAL-001: Re-validate token inside the transaction with select_for_update()
            # to close the TOCTOU window (token could be consumed between the GET check
            # and this POST). select_for_update() holds a row-level lock.
            record = PasswordResetToken.objects.select_for_update().filter(
                token_hash=token_hash,
                used=False,
                expires_at__gt=now(),
            ).first()

            if not record:
                raise BusinessException("invalid_or_expired_token")

            user = record.user

            # Validate password INSIDE the transaction (after lock is held)
            validate_user_password(new_password)
            if is_password_reused(user, new_password):
                raise ValidationError({
                    "error": "password_reused",
                    "detail": "Cannot reuse a recent password.",
                })

            if len(new_password.encode("utf-8")) > 72:
                raise ValidationError({"error": "password_too_long", "detail": "Password must not exceed 72 bytes."})

            # Security: mark token consumed BEFORE writing new password.
            record.used = True
            record.save(update_fields=["used"])

            # Invalidate all other active tokens for this user
            PasswordResetToken.objects.filter(user=user, used=False).update(used=True)

            user.password = make_password(new_password)
            user.save(update_fields=["password"])

            PasswordHistory.objects.create(
                user=user,
                password_hash=user.password,
                changed_via="reset",
            )

            transaction.on_commit(lambda: password_changed.send(
                sender=user.__class__,
                user=user,
                ip=ip,
                user_agent=user_agent,
            ))

        logger.info("Password reset completed | user_id=%s | ip=<redacted>", user.pk)
