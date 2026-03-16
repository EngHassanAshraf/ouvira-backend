from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel, SoftDeleteModel

class AttendanceRecord(TimeStampedModel, SoftDeleteModel):
    class StatusChoice(models.TextChoices):
        PRESENT = "present", _("Present")
        ABSENT = "absent", _("Absent")
        HALF_DAY = "half_day", _("Half Day")
        LATE = "late", _("Late")

    # 'hris_core.Employee' deb yozish orqali import xatolaridan qochamiz
    employee = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )
    date = models.DateField(verbose_name=_("Date"))
    check_in_time = models.TimeField(blank=True, null=True)
    check_out_time = models.TimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=StatusChoice.choices)

    class Meta:
        db_table = "hris_attendance_records"
        unique_together = (("employee", "date"),)