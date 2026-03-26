from django.db import models
from django.utils import timezone
from django.conf import settings


class LoginActivity(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="logn_activities",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} logged in at {self.timestamp}"

    class Meta:
        verbose_name = "Login Activity"
        verbose_name_plural = "Login Activities"

class PasswordHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_history",
    )

    password_hash = models.CharField(max_length=255)
    changed_via = models.CharField(max_length=50)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}"

    class Meta:
        ordering = ["-changed_at"]
        verbose_name = "Password History"
        verbose_name_plural = "Passwords Histories"

# ==================== NEW MODELS (Auth Security) ====================

class OTPRecord(models.Model):
    """
    Unified OTP model supporting both email and SMS channels.
    Stores HMAC-SHA256 hash of the OTP — never the plaintext.
    Channel is detected server-side from the identifier format.
    """

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="otp_records",
        help_text="Nullable — OTP may be issued before user account fully exists.",
    )
    identifier = models.CharField(
        max_length=255,
        help_text="Email address or phone number.",
    )
    channel = models.CharField(
        max_length=5,
        choices=Channel.choices,
        help_text="Auto-detected from identifier format.",
    )
    # HMAC-SHA256(SECRET_KEY, raw_otp) — 64-char hex digest
    otp_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"{self.channel}:{self.identifier} ({'verified' if self.is_verified else 'pending'})"

    class Meta:
        db_table = "auth_otp_records"
        verbose_name = "OTP Record"
        verbose_name_plural = "OTP Records"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["identifier", "channel", "is_verified"]),
            models.Index(fields=["identifier", "channel", "expires_at"]),
        ]


class PasswordResetToken(models.Model):
    """
    Single-use password reset token.
    Stores SHA-256 hash of the raw token — raw token is sent via email/SMS once.
    A partial unique index (enforced in migration) guarantees at most one
    active (used=False) token per user at the database level.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    # SHA-256(raw_token) — 64-char hex digest
    token_hash = models.CharField(max_length=64, db_index=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    def __str__(self):
        return f"PasswordResetToken for {self.user} ({'used' if self.used else 'active'})"

    class Meta:
        db_table = "auth_password_reset_tokens"
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "used"]),
        ]
