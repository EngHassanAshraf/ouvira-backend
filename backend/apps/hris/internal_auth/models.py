"""
Internal Auth Models
====================
Tracks internal login attempts for audit and lockout purposes.
Separate from the external LoginActivity model so internal and external
audit trails are never mixed.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class InternalLoginAttempt(models.Model):
    """
    Audit record for every internal login attempt (success or failure).
    Used for:
      - Security audit trail
      - Account lockout enforcement (via Redis — this is the persistent record)
      - Compliance reporting
    """

    class Outcome(models.TextChoices):
        SUCCESS = "success", _("Success")
        FAILURE = "failure", _("Failure")
        LOCKED = "locked", _("Locked Out")

    # Nullable — we record failures even when user is not found
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="internal_login_attempts",
    )
    identifier = models.CharField(
        max_length=255,
        help_text="Email or username used in the login attempt (stored for audit).",
    )
    company_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Company context resolved at login time.",
    )
    outcome = models.CharField(max_length=20, choices=Outcome.choices)
    failure_reason = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "internal_auth_login_attempts"
        verbose_name = _("Internal Login Attempt")
        verbose_name_plural = _("Internal Login Attempts")
        indexes = [
            models.Index(fields=["identifier", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["outcome", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.identifier} | {self.outcome} | {self.created_at}"
