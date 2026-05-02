from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from .trip_request import BusinessTripRequest


class BusinessTripActivityLog(TimeStampedModel):
    """
    Xizmat safari so'roviga oid barcha amallar tarixi.
    Kim, qachon, nima qildi — hammasi shu yerda.

    Full action history for a business trip request.
    Who did what and when — all recorded here.
    """

    class ActionChoice(models.TextChoices):
        SUBMITTED        = "submitted",        _("Submitted")
        UPDATED          = "updated",          _("Updated")
        MANAGER_APPROVED = "manager_approved", _("Manager Approved")
        HR_APPROVED      = "hr_approved",      _("HR Approved")
        DECLINED         = "declined",         _("Declined")
        CANCELLED        = "cancelled",        _("Cancelled")
        INTERRUPTED      = "interrupted",      _("Interrupted")
        ACTIVATED        = "activated",        _("Activated")
        COMPLETED        = "completed",        _("Completed")

    trip_request = models.ForeignKey(
        BusinessTripRequest,
        on_delete=models.CASCADE,
        related_name="activity_logs",
        verbose_name=_("Business Trip Request")
    )
    performed_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        related_name="business_trip_activity_logs",
        verbose_name=_("Performed By")
    )
    action       = models.CharField(
        max_length=20,
        choices=ActionChoice.choices,
        verbose_name=_("Action")
    )
    note         = models.TextField(
        blank=True, null=True,
        verbose_name=_("Note")
    )
    company_id   = models.PositiveIntegerField(
        verbose_name=_("Company ID"),
        help_text=_("Taken from request.tenant.id — multi-tenant support")
    )

    class Meta:
        db_table = "hris_business_trip_activity_logs"
        verbose_name = _("Business Trip Activity Log")
        verbose_name_plural = _("Business Trip Activity Logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["trip_request"]),
            models.Index(fields=["company_id"]),
        ]

    def __str__(self):
        return f"{self.trip_request} | {self.action} | {self.performed_by}"

    