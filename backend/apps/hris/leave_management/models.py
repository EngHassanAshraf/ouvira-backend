from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel, SoftDeleteModel


class LeaveType(TimeStampedModel, SoftDeleteModel):
    name = models.CharField(max_length=100)  # Annual, Sick, Maternity
    code = models.SlugField(max_length=20, unique=True)
    days_per_year = models.IntegerField(default=21)

    class Meta:
        db_table = "hris_leave_types"


class LeaveRequest(TimeStampedModel, SoftDeleteModel):
    class StatusChoice(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")

    employee = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="leave_requests"
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=StatusChoice.choices, default=StatusChoice.PENDING)
    reason = models.TextField(blank=True, null=True)

    # Kim tasdiqladi?
    approved_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="approved_leaves"
    )

    class Meta:
        db_table = "hris_leave_requests"