"""
Termination Warning Model

Handles warnings issued before termination:
- Absence warnings (Egyptian Law: 5 days, 10 days)
- Absence warnings (Saudi Law: 5 days, 10 days with registered mail)
- Performance warnings (evaluation-based)
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.models import TimeStampedModel, SoftDeleteModel


class TerminationWarning(TimeStampedModel, SoftDeleteModel):
    """
    Warning model for absence and performance issues.

    Business Rules:
    - Absence: 1st warning at 5 days, 2nd at 10 days
    - Performance: Warning if evaluation < 50% OR two evaluations < 60%
    - Warnings escalate to termination if not resolved
    """

    class WarningType(models.TextChoices):
        ABSENCE_EGYPTIAN = "absence_egyptian", _("Absence Warning (Egyptian Law)")
        ABSENCE_SAUDI = "absence_saudi", _("Absence Warning (Saudi Law)")
        PERFORMANCE = "performance", _("Performance Warning")

    class WarningLevel(models.TextChoices):
        FIRST = "first", _("First Warning")
        SECOND = "second", _("Second Warning (Final)")

    class Status(models.TextChoices):
        ISSUED = "issued", _("Issued")
        ACKNOWLEDGED = "acknowledged", _("Acknowledged by Employee")
        RESOLVED = "resolved", _("Resolved")
        ESCALATED = "escalated", _("Escalated to Termination")

    # Core fields
    employee = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="termination_warnings",
        verbose_name=_("Employee")
    )

    warning_type = models.CharField(
        max_length=30,
        choices=WarningType.choices,
        verbose_name=_("Warning Type")
    )

    warning_level = models.CharField(
        max_length=10,
        choices=WarningLevel.choices,
        verbose_name=_("Warning Level")
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ISSUED,
        verbose_name=_("Status")
    )

    # Warning details
    reason = models.TextField(
        verbose_name=_("Reason"),
        help_text=_("Detailed explanation of the issue")
    )

    issue_date = models.DateField(
        default=timezone.now,
        verbose_name=_("Issue Date")
    )

    # For absence warnings
    absence_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Absence Start Date"),
        help_text=_("First day of unexcused absence")
    )

    absence_days_count = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Absence Days Count"),
        help_text=_("Total consecutive unexcused absence days")
    )

    # For performance warnings
    evaluation_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Evaluation Score"),
        help_text=_("Performance evaluation score (0-100)")
    )

    evaluation_period = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Evaluation Period"),
        help_text=_("e.g., Q1 2025, Annual 2024")
    )

    # Delivery method (for legal compliance)
    sent_via_registered_mail = models.BooleanField(
        default=False,
        verbose_name=_("Sent via Registered Mail"),
        help_text=_("Required for 2nd warning in Saudi Law")
    )

    registered_mail_tracking = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Registered Mail Tracking Number")
    )

    # Employee acknowledgment
    acknowledged_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Acknowledged Date")
    )

    employee_response = models.TextField(
        blank=True,
        verbose_name=_("Employee Response"),
        help_text=_("Employee's statement or explanation")
    )

    # Issued by
    issued_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        related_name="issued_warnings",
        verbose_name=_("Issued By")
    )

    # Resolution
    resolved_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Resolved Date")
    )

    resolution_notes = models.TextField(
        blank=True,
        verbose_name=_("Resolution Notes")
    )

    # Escalation to termination
    escalated_to_termination = models.ForeignKey(
        "TerminationRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="warnings",
        verbose_name=_("Escalated to Termination")
    )

    escalation_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Escalation Date")
    )

    # Attachments
    attachment = models.FileField(
        upload_to="termination_warnings/%Y/%m/",
        null=True,
        blank=True,
        verbose_name=_("Attachment"),
        help_text=_("Warning letter, medical reports, evaluation documents")
    )

    # Form S6 (Egyptian Law specific)
    form_s6_attached = models.BooleanField(
        default=False,
        verbose_name=_("Form S6 Attached"),
        help_text=_("Required for Egyptian Labor Law compliance")
    )

    class Meta:
        db_table = "hris_termination_warnings"
        ordering = ["-issue_date"]
        indexes = [
            models.Index(fields=["employee", "warning_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["issue_date"]),
        ]
        verbose_name = _("Termination Warning")
        verbose_name_plural = _("Termination Warnings")

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_warning_type_display()} ({self.get_warning_level_display()})"

    def clean(self):
        """Validation rules"""
        super().clean()

        # Absence warnings must have absence details
        if self.warning_type in [self.WarningType.ABSENCE_EGYPTIAN, self.WarningType.ABSENCE_SAUDI]:
            if not self.absence_start_date or not self.absence_days_count:
                raise ValidationError({
                    "absence_start_date": _("Absence start date and days count required for absence warnings")
                })

            # Validate absence days based on warning level
            if self.warning_level == self.WarningLevel.FIRST and self.absence_days_count < 5:
                raise ValidationError({
                    "absence_days_count": _("First warning requires at least 5 days of absence")
                })

            if self.warning_level == self.WarningLevel.SECOND and self.absence_days_count < 10:
                raise ValidationError({
                    "absence_days_count": _("Second warning requires at least 10 days of absence")
                })

        # Performance warnings must have evaluation score
        if self.warning_type == self.WarningType.PERFORMANCE:
            if self.evaluation_score is None:
                raise ValidationError({
                    "evaluation_score": _("Evaluation score required for performance warnings")
                })

            # Validate score range
            if not (0 <= self.evaluation_score <= 100):
                raise ValidationError({
                    "evaluation_score": _("Evaluation score must be between 0 and 100")
                })

        # Saudi Law 2nd warning must be sent via registered mail
        if (self.warning_type == self.WarningType.ABSENCE_SAUDI
            and self.warning_level == self.WarningLevel.SECOND
            and not self.sent_via_registered_mail):
            raise ValidationError({
                "sent_via_registered_mail": _("Saudi Law requires 2nd warning via registered mail")
            })

        # Egyptian Law must have Form S6 attached
        if (self.warning_type == self.WarningType.ABSENCE_EGYPTIAN
            and not self.form_s6_attached
            and self.status != self.Status.ISSUED):
            raise ValidationError({
                "form_s6_attached": _("Form S6 must be attached for Egyptian Law warnings")
            })

    def save(self, *args, **kwargs):
        """Auto-set fields on save"""

        # Set acknowledged_date when status changes to ACKNOWLEDGED
        if self.status == self.Status.ACKNOWLEDGED and not self.acknowledged_date:
            self.acknowledged_date = timezone.now()

        # Set resolved_date when status changes to RESOLVED
        if self.status == self.Status.RESOLVED and not self.resolved_date:
            self.resolved_date = timezone.now()

        # Set escalation_date when status changes to ESCALATED
        if self.status == self.Status.ESCALATED and not self.escalation_date:
            self.escalation_date = timezone.now()

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_final_warning(self):
        """Check if this is a final warning (2nd level)"""
        return self.warning_level == self.WarningLevel.SECOND

    @property
    def can_escalate_to_termination(self):
        """Check if warning can be escalated to termination"""
        return (
            self.status == self.Status.ISSUED
            and self.is_final_warning
            and not self.escalated_to_termination
        )