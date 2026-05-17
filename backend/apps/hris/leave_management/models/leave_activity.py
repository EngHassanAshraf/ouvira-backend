from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from .leave_request import LeaveRequest


class LeaveActivityLog(TimeStampedModel):
    """
    Ta'til so'roviga oid barcha amallar tarixi.
    Kim, qachon, nima qildi — hammasi shu yerda.
    """

    class ActionChoice(models.TextChoices):
        SUBMITTED   = "submitted",   _("Submitted")
        UPDATED     = "updated",     _("Updated")
        APPROVED    = "approved",    _("Approved")
        DECLINED    = "declined",    _("Declined")
        CANCELLED   = "cancelled",   _("Cancelled")
        INTERRUPTED = "interrupted", _("Interrupted")
        VIEWED      = "viewed",      _("Viewed")
        DELETED     = "deleted",     _("Deleted")

    leave_request = models.ForeignKey(
        LeaveRequest,
        on_delete=models.CASCADE,
        related_name="activity_logs"
    )
    performed_by  = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        related_name="leave_activity_logs"
    )
    action        = models.CharField(
        max_length=20,
        choices=ActionChoice.choices,
        verbose_name=_("Action")
    )
    note          = models.TextField(
        blank=True, null=True,
        verbose_name=_("Note")
    )

    class Meta:
        db_table = "hris_leave_activity_logs"
        verbose_name = _("Leave Activity Log")
        verbose_name_plural = _("Leave Activity Logs")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.leave_request} | {self.action} | {self.performed_by}"