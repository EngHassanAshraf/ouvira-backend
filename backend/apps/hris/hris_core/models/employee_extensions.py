"""
Employee extension models:
  - EmployeeLeaveBalance
  - EmployeeAllowance
  - EmployeeBankDetail
  - EmployeeCost
  - EmployeeDocument
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel, SoftDeleteModel


class EmployeeLeaveBalance(TimeStampedModel, SoftDeleteModel):
    """Per-employee leave balance per leave type."""

    employee = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="leave_balances",
        verbose_name=_("Employee"),
    )
    leave_type = models.ForeignKey(
        "hris_leave_management.LeaveType",
        on_delete=models.PROTECT,
        related_name="employee_balances",
        verbose_name=_("Leave Type"),
    )
    total_days = models.DecimalField(
        max_digits=6, decimal_places=2, default=0, verbose_name=_("Total Days")
    )
    used_days = models.DecimalField(
        max_digits=6, decimal_places=2, default=0, verbose_name=_("Used Days")
    )
    reset_date = models.DateField(
        blank=True, null=True, verbose_name=_("Balance Reset Date")
    )

    class Meta:
        db_table = "hris_employee_leave_balances"
        verbose_name = _("Employee Leave Balance")
        verbose_name_plural = _("Employee Leave Balances")
        unique_together = (("employee", "leave_type"),)

    def __str__(self):
        return f"{self.employee} — {self.leave_type} ({self.remaining_days} days left)"

    @property
    def remaining_days(self):
        return self.total_days - self.used_days


class EmployeeAllowance(TimeStampedModel, SoftDeleteModel):
    """Custom monetary allowances per employee (transport, housing, etc.)."""

    employee = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="allowances",
        verbose_name=_("Employee"),
    )
    name = models.CharField(max_length=255, verbose_name=_("Allowance Name"))
    value = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Allowance Value")
    )

    class Meta:
        db_table = "hris_employee_allowances"
        verbose_name = _("Employee Allowance")
        verbose_name_plural = _("Employee Allowances")

    def __str__(self):
        return f"{self.employee} — {self.name}: {self.value}"


class EmployeeBankDetail(TimeStampedModel, SoftDeleteModel):
    """Bank account details for payroll."""

    employee = models.OneToOneField(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="bank_detail",
        verbose_name=_("Employee"),
    )
    bank_iban = models.CharField(
        max_length=34, verbose_name=_("Bank IBAN Number")
    )
    bank_name = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Bank Name")
    )

    class Meta:
        db_table = "hris_employee_bank_details"
        verbose_name = _("Employee Bank Detail")
        verbose_name_plural = _("Employee Bank Details")

    def __str__(self):
        return f"{self.employee} — {self.bank_name} ({self.bank_iban})"


class EmployeeCost(TimeStampedModel, SoftDeleteModel):
    """Tracks additional costs associated with an employee (training, equipment, etc.)."""

    employee = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="costs",
        verbose_name=_("Employee"),
    )
    cost_type = models.CharField(max_length=255, verbose_name=_("Cost Type"))
    value = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Cost Value")
    )
    cost_date = models.DateField(verbose_name=_("Cost Date"))

    class Meta:
        db_table = "hris_employee_costs"
        verbose_name = _("Employee Cost")
        verbose_name_plural = _("Employee Costs")
        ordering = ["-cost_date"]

    def __str__(self):
        return f"{self.employee} — {self.cost_type}: {self.value} on {self.cost_date}"


class EmployeeDocument(TimeStampedModel, SoftDeleteModel):
    """Official documents attached to an employee (passport scan, ID copy, etc.)."""

    class DocumentType(models.TextChoices):
        PASSPORT = "passport", _("Passport")
        NATIONAL_ID = "national_id", _("National ID")
        IQAMA = "iqama", _("Iqama / Residency Permit")
        VISA = "visa", _("Visa")
        CONTRACT = "contract", _("Employment Contract")
        CERTIFICATE = "certificate", _("Certificate")
        OTHER = "other", _("Other")

    employee = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("Employee"),
    )
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
        verbose_name=_("Document Type"),
    )
    file = models.FileField(
        upload_to="employees/documents/",
        verbose_name=_("Document File"),
    )
    file_name = models.CharField(
        max_length=255, blank=True, verbose_name=_("File Name")
    )

    class Meta:
        db_table = "hris_employee_documents"
        verbose_name = _("Employee Document")
        verbose_name_plural = _("Employee Documents")

    def save(self, *args, **kwargs):
        if self.file and not self.file_name:
            self.file_name = self.file.name.split("/")[-1]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} — {self.file_name}"


class EmployeeBusinessTripBalance(TimeStampedModel, SoftDeleteModel):
    """Business trip allowance balance per employee."""

    employee = models.OneToOneField(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="business_trip_balance",
        verbose_name=_("Employee"),
    )
    total_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name=_("Total Balance")
    )
    used_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name=_("Used Balance")
    )
    reset_date = models.DateField(
        blank=True, null=True, verbose_name=_("Balance Reset Date")
    )

    class Meta:
        db_table = "hris_employee_business_trip_balances"
        verbose_name = _("Employee Business Trip Balance")
        verbose_name_plural = _("Employee Business Trip Balances")

    def __str__(self):
        return f"{self.employee} — Business Trip ({self.remaining_balance} remaining)"

    @property
    def remaining_balance(self):
        return self.total_balance - self.used_balance
