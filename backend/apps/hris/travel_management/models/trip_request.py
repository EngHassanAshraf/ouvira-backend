from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from apps.core.models import TimeStampedModel, SoftDeleteModel
from .trip_benefit import BusinessTripBenefit


class BusinessTripRequest(TimeStampedModel, SoftDeleteModel):
    """
    Xodimning xizmat safari so'rovi.
    2 bosqichli tasdiqlash: Manager → HR Director.
    Manager xodim nomidan so'rov yarata oladi (on_behalf_of).

    Employee's business trip request.
    2-step approval: Manager → HR Director.
    Manager can create a request on behalf of an employee.
    """

    class StatusChoice(models.TextChoices):
        PENDING          = "pending",          _("Pending")
        MANAGER_APPROVED = "manager_approved", _("Manager Approved")
        APPROVED         = "approved",         _("Approved")
        ACTIVE           = "active",           _("Active")
        COMPLETED        = "completed",        _("Completed")
        DECLINED         = "declined",         _("Declined")
        CANCELLED        = "cancelled",        _("Cancelled")
        INTERRUPTED      = "interrupted",      _("Interrupted")

    # --- Asosiy ma'lumotlar / Core info ---
    employee    = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="business_trip_requests",
        verbose_name=_("Employee")
    )
    created_by  = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_business_trip_requests",
        verbose_name=_("Created By"),
        help_text=_("If manager submitted on behalf of employee")
    )
    destination = models.CharField(
        max_length=255,
        verbose_name=_("Destination")
    )
    start_date  = models.DateField(verbose_name=_("Start Date"))
    end_date    = models.DateField(verbose_name=_("End Date"))
    duration    = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Duration (days)"),
        help_text=_("Auto calculated: end_date - start_date + 1")
    )
    details     = models.TextField(
        blank=True, null=True,
        verbose_name=_("Details"),
        help_text=_("Max 1000 characters")
    )
    benefits    = models.ManyToManyField(
        BusinessTripBenefit,
        blank=True,
        related_name="trip_requests",
        verbose_name=_("Benefits")
    )
    attachments = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Attachments"),
        help_text=_("List of file URLs")
    )
    status      = models.CharField(
        max_length=20,
        choices=StatusChoice.choices,
        default=StatusChoice.PENDING,
        verbose_name=_("Status")
    )
    company_id  = models.PositiveIntegerField(
        verbose_name=_("Company ID"),
        help_text=_("Taken from request.tenant.id — multi-tenant support")
    )

    # --- 1-bosqich: Manager / Step 1: Manager ---
    manager_approved_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="manager_approved_trips",
        verbose_name=_("Manager Approved By")
    )
    manager_approved_at = models.DateTimeField(null=True, blank=True)

    # --- 2-bosqich: HR Director / Step 2: HR Director ---
    hr_approved_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="hr_approved_trips",
        verbose_name=_("HR Approved By")
    )
    hr_approved_at = models.DateTimeField(null=True, blank=True)

    # --- Rad etish / Decline ---
    declined_by    = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="declined_trips",
        verbose_name=_("Declined By")
    )
    declined_at    = models.DateTimeField(null=True, blank=True)
    decline_reason = models.TextField(
        blank=True, null=True,
        verbose_name=_("Decline Reason")
    )

    # --- Bekor qilish / Cancellation ---
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # --- To'xtatish / Interruption ---
    interrupted_by   = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="interrupted_trips",
        verbose_name=_("Interrupted By")
    )
    interrupted_at   = models.DateTimeField(null=True, blank=True)
    interruption_date = models.DateField(
        null=True, blank=True,
        verbose_name=_("Interruption Date"),
        help_text=_("The date when the trip was manually interrupted")
    )

    class Meta:
        db_table = "hris_business_trip_requests"
        verbose_name = _("Business Trip Request")
        verbose_name_plural = _("Business Trip Requests")
        indexes = [
            models.Index(fields=["employee", "status"]),
            models.Index(fields=["employee", "start_date", "end_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["company_id"]),
        ]

    def __str__(self):
        return f"{self.employee} | {self.destination} | {self.start_date} → {self.end_date}"

    def save(self, *args, **kwargs):
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