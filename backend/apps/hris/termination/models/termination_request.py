"""
Termination Request Model

Handles all types of employment terminations:
- Resignation (voluntary)
- Behavioral termination
- Performance termination
- Probation termination
- Medical termination
- Layoff
- Deceased employee processing
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from apps.core.models import TimeStampedModel, SoftDeleteModel


class TerminationRequest(TimeStampedModel, SoftDeleteModel):
    """
    Main model for all termination requests and resignations.

    Workflow:
    1. Employee submits resignation OR HR initiates termination
    2. Manager reviews and approves
    3. GM (General Manager) gives final approval
    4. HR processes termination (settlement, exit interview)
    5. Employee can withdraw resignation within 7 days
    """

    class TerminationType(models.TextChoices):
        RESIGNATION = "resignation", _("Resignation (Voluntary)")
        BEHAVIORAL = "behavioral", _("Behavioral Violation")
        PERFORMANCE = "performance", _("Poor Performance")
        PROBATION = "probation", _("Probation Termination")
        MEDICAL = "medical", _("Medical Termination")
        LAYOFF = "layoff", _("Layoff/Restructuring")
        DECEASED = "deceased", _("Deceased Employee")
        ABSENCE = "absence", _("Absence (After Warnings)")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        SUBMITTED = "submitted", _("Submitted")
        MANAGER_APPROVED = "manager_approved", _("Manager Approved")
        GM_APPROVED = "gm_approved", _("GM Approved")
        PROCESSED = "processed", _("Processed")
        WITHDRAWN = "withdrawn", _("Withdrawn")
        REJECTED = "rejected", _("Rejected")

    # Core fields
    employee = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="termination_requests",
        verbose_name=_("Employee")
    )

    termination_type = models.CharField(
        max_length=20,
        choices=TerminationType.choices,
        verbose_name=_("Termination Type")
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("Status")
    )

    # Reason and details
    reason = models.TextField(
        verbose_name=_("Reason for Termination"),
        help_text=_("Detailed explanation")
    )

    is_voluntary = models.BooleanField(
        default=False,
        verbose_name=_("Is Voluntary"),
        help_text=_("True for resignation, False for company-initiated")
    )

    # Dates
    submission_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Submission Date")
    )

    final_working_day = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Final Working Day"),
        help_text=_("Last day employee works")
    )

    notice_period_days = models.IntegerField(
        default=30,
        verbose_name=_("Notice Period (Days)"),
        help_text=_("Default 30 days for resignation")
    )

    # Approvals
    requested_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="initiated_terminations",
        verbose_name=_("Requested By"),
        help_text=_("Employee (for resignation) or HR (for termination)")
    )

    approved_by_manager = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manager_approved_terminations",
        verbose_name=_("Approved by Manager")
    )

    manager_approval_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Manager Approval Date")
    )

    approved_by_gm = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gm_approved_terminations",
        verbose_name=_("Approved by GM")
    )

    gm_approval_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("GM Approval Date")
    )

    # Rejection
    rejected_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_terminations",
        verbose_name=_("Rejected By")
    )

    rejection_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Rejection Date")
    )

    rejection_reason = models.TextField(
        blank=True,
        verbose_name=_("Rejection Reason")
    )

    # Withdrawal (for resignations only)
    withdrawal_request_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Withdrawal Request Date")
    )

    withdrawal_reason = models.TextField(
        blank=True,
        verbose_name=_("Withdrawal Reason")
    )

    # Processing
    processed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Processed Date")
    )

    processed_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_terminations",
        verbose_name=_("Processed By")
    )

    # Additional details
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Internal notes for HR")
    )

    attachment = models.FileField(
        upload_to="terminations/%Y/%m/",
        null=True,
        blank=True,
        verbose_name=_("Attachment"),
        help_text=_("Supporting documents (resignation letter, medical reports, etc.)")
    )

    class Meta:
        db_table = "hris_termination_requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["employee", "status"]),
            models.Index(fields=["termination_type", "status"]),
            models.Index(fields=["submission_date"]),
        ]
        verbose_name = _("Termination Request")
        verbose_name_plural = _("Termination Requests")

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_termination_type_display()} ({self.get_status_display()})"

    def clean(self):
        """Validation rules"""
        super().clean()

        # Resignation must be voluntary
        if self.termination_type == self.TerminationType.RESIGNATION and not self.is_voluntary:
            raise ValidationError({
                "is_voluntary": _("Resignation must be marked as voluntary")
            })

        # Non-resignation should not be voluntary
        if self.termination_type != self.TerminationType.RESIGNATION and self.is_voluntary:
            raise ValidationError({
                "is_voluntary": _("Only resignation can be voluntary")
            })

        # Final working day should be after submission
        if self.submission_date and self.final_working_day:
            if self.final_working_day < self.submission_date:
                raise ValidationError({
                    "final_working_day": _("Final working day cannot be before submission date")
                })

    def save(self, *args, **kwargs):
        """Auto-set fields on save"""

        # Set submission_date when status changes to SUBMITTED
        if self.status == self.Status.SUBMITTED and not self.submission_date:
            self.submission_date = timezone.now().date()

        # Auto-calculate final_working_day for resignation (30 days after submission)
        if (self.termination_type == self.TerminationType.RESIGNATION
                and self.submission_date
                and not self.final_working_day):
            self.final_working_day = self.submission_date + timedelta(days=self.notice_period_days)

        # Set processed_date when status is PROCESSED
        if self.status == self.Status.PROCESSED and not self.processed_date:
            self.processed_date = timezone.now()

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def can_be_withdrawn(self):
        """
        Check if resignation can be withdrawn.
        Rule: Within 7 working days of submission.
        """
        if self.termination_type != self.TerminationType.RESIGNATION:
            return False

        if self.status not in [self.Status.SUBMITTED, self.Status.MANAGER_APPROVED]:
            return False

        if not self.submission_date:
            return False

        days_since_submission = (timezone.now().date() - self.submission_date).days
        return days_since_submission <= 7

    @property
    def days_until_final_working_day(self):
        """Calculate days remaining until final working day"""
        if not self.final_working_day:
            return None

        delta = self.final_working_day - timezone.now().date()
        return delta.days if delta.days >= 0 else 0

    @property
    def requires_exit_interview(self):
        """Check if exit interview is required"""
        return self.status in [
            self.Status.GM_APPROVED,
            self.Status.PROCESSED
        ] and self.termination_type != self.TerminationType.DECEASED