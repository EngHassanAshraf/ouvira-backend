from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel, SoftDeleteModel
from .employee import Employee
from .organization import Position


class Employment(TimeStampedModel, SoftDeleteModel):
    class StatusChoice(models.TextChoices):
        ACTIVE = "active", _("Active")
        PROBATION = "probation", _("Probation")
        ON_LEAVE = "on_leave", _("On Leave")
        BUSINESS_TRIP = "business_trip", _("Business Trip")
        TERMINATED = "terminated", _("Terminated")

    class TypeChoice(models.TextChoices):
        FULL_TIME = "full_time", _("Full-Time")
        PART_TIME = "part_time", _("Part-Time")
        CONTRACT = "contract", _("Contract")
        FIXED_PRICE = "fixed_price", _("Fixed-Price Contract")

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="employments",
    )
    hire_date = models.DateField(verbose_name=_("Hire Date"))
    status = models.CharField(
        max_length=20,
        choices=StatusChoice.choices,
        default=StatusChoice.PROBATION,
    )
    employment_type = models.CharField(
        max_length=20,
        choices=TypeChoice.choices,
        default=TypeChoice.FULL_TIME,
    )

    # KSA contract dates
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "hris_employments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["employee", "status"], name="hris_employment_emp_status_idx"),
            models.Index(fields=["status"], name="hris_employment_status_idx"),
        ]

    def __str__(self):
        return f"{self.employee} — {self.get_status_display()}"


class EmployeeAssignment(TimeStampedModel, SoftDeleteModel):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="assignments"
    )
    position = models.ForeignKey(
        Position, on_delete=models.PROTECT, related_name="assignments"
    )
    start_date = models.DateField()
    is_primary = models.BooleanField(default=True)

    class Meta:
        db_table = "hris_employee_assignments"
