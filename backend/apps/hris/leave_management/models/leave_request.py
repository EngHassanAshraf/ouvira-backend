from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from apps.core.models import TimeStampedModel, SoftDeleteModel
from .leave_type import LeaveType


class LeaveRequest(TimeStampedModel, SoftDeleteModel):
    """
    Xodimning ta'til so'rovi.
    2 bosqichli tasdiqlash: Direct Manager → HR Director
    """

    class StatusChoice(models.TextChoices):
        PENDING          = "pending",          _("Pending")
        MANAGER_APPROVED = "manager_approved", _("Manager Approved")
        APPROVED         = "approved",         _("Approved")
        DECLINED         = "declined",         _("Declined")
        CANCELLED        = "cancelled",        _("Cancelled")
        INTERRUPTED      = "interrupted",      _("Interrupted")

    # --- Asosiy ma'lumotlar ---
    employee   = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="leave_requests",
        verbose_name=_("Employee")
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        verbose_name=_("Leave Type")
    )
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date   = models.DateField(verbose_name=_("End Date"))
    duration   = models.IntegerField(
        default=0,
        verbose_name=_("Duration (days)"),
        help_text=_("Auto calculated: end_date - start_date + 1")
    )
    details    = models.TextField(
        blank=True, null=True,
        verbose_name=_("Details"),
        help_text=_("Max 1000 characters")
    )
    attachment = models.FileField(
        upload_to="leave_attachments/%Y/%m/",
        blank=True, null=True,
        verbose_name=_("Attachment"),
        help_text=_("PDF, JPG, PNG, DOCX — max 5MB")
    )
    status     = models.CharField(
        max_length=20,
        choices=StatusChoice.choices,
        default=StatusChoice.PENDING,
        verbose_name=_("Status")
    )

    # --- Menejer behalf uchun ---
    created_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_leave_requests",
        verbose_name=_("Created By"),
        help_text=_("If manager submitted on behalf of employee")
    )

    # --- 1-bosqich: Direct Manager ---
    manager_approved_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="manager_approved_leaves",
        verbose_name=_("Manager Approved By")
    )
    manager_approved_at = models.DateTimeField(null=True, blank=True)

    # --- 2-bosqich: HR Director ---
    hr_approved_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="hr_approved_leaves",
        verbose_name=_("HR Approved By")
    )
    hr_approved_at = models.DateTimeField(null=True, blank=True)

    # --- Rad etish ---
    declined_by    = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="declined_leaves",
        verbose_name=_("Declined By")
    )
    declined_at    = models.DateTimeField(null=True, blank=True)
    decline_reason = models.TextField(blank=True, null=True, verbose_name=_("Decline Reason"))

    # --- To'xtatish (Interruption) ---
    interrupted_by    = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="interrupted_leaves",
        verbose_name=_("Interrupted By")
    )
    interruption_date = models.DateField(null=True, blank=True, verbose_name=_("Interruption Date"))
    interrupted_at    = models.DateTimeField(null=True, blank=True)

    # --- Bekor qilish ---
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "hris_leave_requests"
        verbose_name = _("Leave Request")
        verbose_name_plural = _("Leave Requests")
        indexes = [
            models.Index(fields=["employee", "status"]),
            models.Index(fields=["employee", "start_date", "end_date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.employee} | {self.leave_type} | {self.start_date} → {self.end_date}"

    def save(self, *args, **kwargs):
        # Duration avtomatik hisoblanadi
        if self.start_date and self.end_date:
            self.duration = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)

    def clean(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError(
                    _("End date must be the same as or later than the start date.")
                )
        if self.details and len(self.details) > 1000:
            raise ValidationError(_("Details must not exceed 1000 characters."))