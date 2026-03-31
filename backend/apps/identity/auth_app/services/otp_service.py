"""
OTP Service — Handles OTP generation, validation, and management.

Supports both email and SMS channels via a unified OTPRecord model.
Channel is auto-detected server-side from the identifier format.
All OTP hashes are HMAC-SHA256 — plaintext is never stored.
"""

import hmac
import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.identity.auth_app.models import OTPRecord
from apps.identity.auth_app.utils import validate_user_email, validate_user_mobile
from apps.shared.exceptions import BusinessException
from apps.shared.messages.error import ERROR_MESSAGES

logger = logging.getLogger(__name__)

# ==================== CONSTANTS ====================

OTP_EXPIRY_MINUTES = 10
MAX_ATTEMPTS = 5
LOCK_MINUTES = 15

# Redis key templates
OTP_RATE_KEY = "otp_rate:{identifier}"           # no channel prefix — identifier is self-discriminating
OTP_ATTEMPTS_KEY = "otp_attempts:{identifier}"   # no channel prefix


def _compute_otp_hash(raw_otp: str) -> str:
    """
    HMAC-SHA256(SECRET_KEY, raw_otp) — 64-char hex string.
    Uses the Django SECRET_KEY as the HMAC key.
    """
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        raw_otp.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class OTPService:
    """Service for OTP operations using HMAC-hashed OTPRecord model."""

    # -------- Channel detection --------

    @staticmethod
    def detect_channel(identifier: str) -> str:
        """
        Determine whether identifier is an email or phone number.
        Uses the existing validators from utils.py — no new regex logic.

        Returns:
            'email' or 'sms'

        Raises:
            BusinessException with 400 if format matches neither.
        """
        try:
            validate_user_email(identifier)
            return OTPRecord.Channel.EMAIL
        except (DjangoValidationError, DRFValidationError):
            pass  # AUTH-005: catch specific validation errors only

        try:
            validate_user_mobile(identifier)
            return OTPRecord.Channel.SMS
        except (DjangoValidationError, DRFValidationError):
            pass  # AUTH-005: catch specific validation errors only

        raise BusinessException("Invalid identifier — must be a valid email or phone number.")

    # -------- OTP generation --------

    @staticmethod
    def generate_and_send(identifier: str) -> None:
        """
        Auto-detect channel, generate a CSPRNG OTP, hash it, persist OTPRecord,
        then dispatch delivery (email or SMS) asynchronously.

        Rate-limit: 1 request per minute per identifier (Redis TTL=60s).
        Always returns None — caller should always respond HTTP 200.
        """
        # DOS-001: Atomic rate-limit check — cache.add() sets only if key absent (atomic)
        rate_key = OTP_RATE_KEY.format(identifier=identifier)
        if not cache.add(rate_key, 1, timeout=60):
            raise BusinessException("Too many OTP requests. Please wait before requesting another.")

        channel = OTPService.detect_channel(identifier)

        raw_otp = str(secrets.randbelow(900000) + 100000)  # Cryptographically secure 6-digit
        otp_hash = _compute_otp_hash(raw_otp)
        expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

        # AUTH-006: Wrap delete + create in a single atomic block so a failed create
        # cannot leave the user with no active OTP record.
        print(f"Testing: {'='*10} raw otp", raw_otp)
        with transaction.atomic():
            # Purge any previous unverified record for this identifier
            OTPRecord.objects.filter(identifier=identifier, is_verified=False).delete()

            otp = OTPRecord.objects.create(
                identifier=identifier,
                channel=channel,
                otp_hash=otp_hash,
                expires_at=expires_at,
            )
        logger.info("OTP issued | channel=%s | identifier=<redacted>", channel)
        # Dispatch delivery asynchronously — import here to avoid circular imports
        OTPService._dispatch(channel, identifier, raw_otp)


    # --------- Dispatch OTP delivery ---------

    @staticmethod
    def _dispatch(channel: str, identifier: str, raw_otp: str) -> None:
        """Dispatch OTP delivery. Deferred import to avoid circular import on startup."""
        if channel == OTPRecord.Channel.EMAIL:
            try:
                from apps.identity.auth_app.tasks import send_otp_email
                print(f"Dispatching OTP email to {identifier}")
                result = send_otp_email.delay(identifier, raw_otp)
                print(f"Task dispatched: {result.id}")
                logger.info("OTP sent | channel=%s | identifier=<redacted>", channel)
            except Exception as e:
                print(f"FAILED to enqueue: {e}")
                logger.exception("Failed to enqueue OTP email | identifier=<redacted>")
        else:
            try:
                from apps.shared.services.sms_service import send_sms
                sent = send_sms(message=f"Your Ouvira OTP is: {raw_otp}. Expires in 10 minutes.", phone=identifier)
                if sent:
                    logger.info("OTP sent | channel=%s | identifier=<redacted>", channel)
                else:
                    logger.error("Failed to send OTP SMS | identifier=<redacted>")
            except Exception:
                logger.exception("Failed to send OTP SMS | identifier=<redacted>")

    # -------- OTP verification --------

    @staticmethod
    def verify(identifier: str, raw_otp: str) -> bool:
        """
        Verify a submitted OTP against the stored HMAC hash.

        - Auto-detects channel from identifier format.
        - Uses hmac.compare_digest for constant-time comparison.
        - Tracks failed attempts in Redis; locks at MAX_ATTEMPTS.
        - Marks OTPRecord is_verified=True on success (single-use).

        Raises:
            BusinessException on validation failure or lockout.

        Returns:
            The channel ('email' or 'sms') on success — caller uses this
            to know which verified flag to set on the user.
        """
        channel = OTPService.detect_channel(identifier)

        attempts_key = OTP_ATTEMPTS_KEY.format(identifier=identifier)
        attempts = cache.get(attempts_key, 0)

        if attempts >= MAX_ATTEMPTS:
            # Refresh lock for another 15 minutes
            cache.set(attempts_key, attempts, timeout=900)
            raise BusinessException(
                "otp_locked: Too many failed attempts. Try again in 15 minutes."
            )

        record = OTPRecord.objects.filter(
            identifier=identifier,
            channel=channel,
            is_verified=False,
        ).first()

        if not record:
            OTPService._increment_attempts(attempts_key, attempts)
            raise BusinessException("invalid_or_expired_otp")

        if record.is_expired():
            record.delete()
            OTPService._increment_attempts(attempts_key, attempts)
            raise BusinessException("invalid_or_expired_otp")

        computed_hash = _compute_otp_hash(raw_otp)

        # Constant-time comparison — mandatory
        if not hmac.compare_digest(record.otp_hash, computed_hash):
            OTPService._increment_attempts(attempts_key, attempts)
            raise BusinessException("invalid_or_expired_otp")

        # Success — mark single-use and clear attempt counter
        record.is_verified = True
        record.save(update_fields=["is_verified"])
        cache.delete(attempts_key)

        logger.info("OTP verified | channel=%s | identifier=<redacted>", channel)
        return channel  # caller uses this to set email_verified or phone_verified

    # --------- Helper methods ---------

    @staticmethod
    def _increment_attempts(attempts_key: str, current: int) -> None:
        new_count = current + 1
        cache.set(attempts_key, new_count, timeout=LOCK_MINUTES * 60)

    @staticmethod
    def cleanup_expired_otps() -> int:
        """Clean up expired OTPRecord rows. Called by the nightly Celery task."""
        count, _ = OTPRecord.objects.filter(expires_at__lt=timezone.now()).delete()
        logger.info("Cleaned up %d expired OTPRecord rows", count)
        return count
