"""
Termination Settlement Model

Handles calculation and payment of final dues:
- End-of-service benefits
- Unused leave balance
- Pending salary
- Bonuses/allowances
- Deductions
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal

from apps.core.models import TimeStampedModel, SoftDeleteModel


class TerminationSettlement(TimeStampedModel, SoftDeleteModel):
    """
    Final settlement calculation for terminated employees.

    Components:
    - End-of-service benefit (gratuity)
    - Unused leave balance
    - Pending salary
    - Bonuses and allowances
    - Deductions (if any)
    """

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending Calculation")
        CALCULATED = "calculated", _("Calculated")
        APPROVED = "approved", _("Approved")
        PAID = "paid", _("Paid")
        REJECTED = "rejected", _("Rejected")

    # Core fields
    termination_request = models.OneToOneField(
        "TerminationRequest",
        on_delete=models.CASCADE,
        related_name="settlement",
        verbose_name=_("Termination Request")
    )

    employee = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="termination_settlements",
        verbose_name=_("Employee")
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_("Status")
    )

    # Settlement components (SAR currency)

    # 1. End-of-service benefit (gratuity)
    years_of_service = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Years of Service"),
        help_text=_("Total years worked")
    )

    end_of_service_benefit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("End-of-Service Benefit"),
        help_text=_("Gratuity based on years of service")
    )

    # 2. Unused leave
    unused_leave_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Unused Leave Days")
    )

    unused_leave_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Unused Leave Amount")
    )

    # 3. Pending salary
    pending_salary_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Pending Salary Days"),
        help_text=_("Days worked in final month")
    )

    pending_salary_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Pending Salary Amount")
    )

    # 4. Bonuses and allowances
    pending_bonus = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Pending Bonus")
    )

    other_allowances = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Other Allowances"),
        help_text=_("Housing, transport, etc.")
    )

    # 5. Deductions
    advance_payments = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Advance Payments"),
        help_text=_("Salary advances to be deducted")
    )

    loan_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Loan Balance"),
        help_text=_("Outstanding employee loans")
    )

    other_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Other Deductions")
    )

    deduction_notes = models.TextField(
        blank=True,
        verbose_name=_("Deduction Notes"),
        help_text=_("Details of deductions")
    )

    # Totals (auto-calculated)
    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Gross Amount"),
        help_text=_("Total before deductions")
    )

    total_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Total Deductions")
    )

    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Net Amount"),
        help_text=_("Final amount to be paid")
    )

    # Calculation details
    calculated_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Calculated Date")
    )

    calculated_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calculated_settlements",
        verbose_name=_("Calculated By")
    )

    calculation_notes = models.TextField(
        blank=True,
        verbose_name=_("Calculation Notes"),
        help_text=_("Notes on calculation methodology")
    )

    # Approval
    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Approved Date")
    )

    approved_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_settlements",
        verbose_name=_("Approved By")
    )

    # Payment
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Payment Date")
    )

    payment_method = models.CharField(
        max_length=20,
        choices=[
            ("bank_transfer", _("Bank Transfer")),
            ("check", _("Check")),
            ("cash", _("Cash"))
        ],
        blank=True,
        verbose_name=_("Payment Method")
    )

    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Payment Reference"),
        help_text=_("Transaction ID or check number")
    )

    paid_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_payments",
        verbose_name=_("Paid By")
    )

    # For deceased employees
    paid_to_heir = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Paid to Heir"),
        help_text=_("Legal heir name for deceased employees")
    )

    heir_relationship = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Heir Relationship"),
        help_text=_("e.g., Spouse, Child, Parent")
    )

    heir_identification = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Heir Identification"),
        help_text=_("ID number of legal heir")
    )

    # Documentation
    attachment = models.FileField(
        upload_to="termination_settlements/%Y/%m/",
        null=True,
        blank=True,
        verbose_name=_("Attachment"),
        help_text=_("Settlement breakdown, receipts, legal documents")
    )

    class Meta:
        db_table = "hris_termination_settlements"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["employee", "status"]),
            models.Index(fields=["status"]),
            models.Index(fields=["payment_date"]),
        ]
        verbose_name = _("Termination Settlement")
        verbose_name_plural = _("Termination Settlements")

    def __str__(self):
        return f"Settlement - {self.employee.full_name} ({self.get_status_display()})"

    def clean(self):
        """Validation rules"""
        super().clean()

        # If status is APPROVED, must have approved_by and approved_date
        if self.status == self.Status.APPROVED:
            if not self.approved_by:
                raise ValidationError({
                    "approved_by": _("Approved by required for approved settlements")
                })

        # If status is PAID, must have payment details
        if self.status == self.Status.PAID:
            if not self.payment_date:
                raise ValidationError({
                    "payment_date": _("Payment date required for paid settlements")
                })
            if not self.payment_method:
                raise ValidationError({
                    "payment_method": _("Payment method required for paid settlements")
                })
            if not self.paid_by:
                raise ValidationError({
                    "paid_by": _("Paid by required for paid settlements")
                })

        # Deceased employees must have heir information
        if (self.termination_request.termination_type == "deceased"
            and self.status == self.Status.PAID):
            if not self.paid_to_heir or not self.heir_relationship:
                raise ValidationError({
                    "paid_to_heir": _("Heir information required for deceased employee settlements")
                })

        # Net amount cannot be negative
        if self.net_amount < 0:
            raise ValidationError({
                "net_amount": _("Net amount cannot be negative")
            })

    def calculate_totals(self):
        """
        Calculate gross, total deductions, and net amounts.
        This method should be called before saving.
        """
        # Gross amount = all positive components
        self.gross_amount = (
            self.end_of_service_benefit +
            self.unused_leave_amount +
            self.pending_salary_amount +
            self.pending_bonus +
            self.other_allowances
        )

        # Total deductions
        self.total_deductions = (
            self.advance_payments +
            self.loan_balance +
            self.other_deductions
        )

        # Net amount
        self.net_amount = self.gross_amount - self.total_deductions

    def save(self, *args, **kwargs):
        """Auto-set fields on save"""

        # Auto-set employee from termination request
        if not self.employee_id:
            self.employee = self.termination_request.employee

        # Recalculate totals before saving
        self.calculate_totals()

        # Set calculated_date when status changes to CALCULATED
        if self.status == self.Status.CALCULATED and not self.calculated_date:
            self.calculated_date = timezone.now()

        # Set approved_date when status changes to APPROVED
        if self.status == self.Status.APPROVED and not self.approved_date:
            self.approved_date = timezone.now()

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_ready_for_payment(self):
        """Check if settlement is ready for payment"""
        return self.status == self.Status.APPROVED and self.net_amount > 0

    @property
    def payment_deadline(self):
        """
        Calculate payment deadline.
        Rule: 1 week after employee death for deceased, otherwise final working day.
        """
        if self.termination_request.termination_type == "deceased":
            # 1 week after termination request submission
            if self.termination_request.submission_date:
                from datetime import timedelta
                return self.termination_request.submission_date + timedelta(days=7)

        # For all others, final working day
        return self.termination_request.final_working_day