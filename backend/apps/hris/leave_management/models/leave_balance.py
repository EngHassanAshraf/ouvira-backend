from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from .leave_type import LeaveType


class LeaveBalance(TimeStampedModel):
    """
    Xodimning har ta'til turi bo'yicha yillik balansi.
    Total / Used / Adjusted / Remaining
    """
    employee   = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="lm_leave_balances",
        verbose_name=_("Employee")
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        verbose_name=_("Leave Type")
    )
    year       = models.IntegerField(verbose_name=_("Year"))

    total_days    = models.DecimalField(
        max_digits=5, decimal_places=1,
        default=0,
        verbose_name=_("Total Days")
    )
    used_days     = models.DecimalField(
        max_digits=5, decimal_places=1,
        default=0,
        verbose_name=_("Used Days")
    )
    adjusted_days = models.DecimalField(
        max_digits=5, decimal_places=1,
        default=0,
        verbose_name=_("Adjusted Days"),
        help_text=_("+/- days adjusted by manager")
    )

    class Meta:
        db_table = "hris_leave_balances"
        verbose_name = _("Leave Balance")
        verbose_name_plural = _("Leave Balances")
        unique_together = (("employee", "leave_type", "year"),)
        indexes = [
            models.Index(fields=["employee", "year"]),
        ]

    def __str__(self):
        return f"{self.employee} | {self.leave_type} | {self.year}"

    @property
    def remaining_days(self):
        """Qolgan kunlar: Total + Adjusted - Used"""
        return self.total_days + self.adjusted_days - self.used_days


class LeaveBalanceAdjustment(TimeStampedModel):
    """
    Menejer tomonidan qo'lda o'zgartirilgan balans tarixi.
    Har bir +/- operatsiya alohida yoziladi.
    """
    balance     = models.ForeignKey(
        LeaveBalance,
        on_delete=models.CASCADE,
        related_name="adjustments"
    )
    adjusted_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        related_name="leave_adjustments_made"
    )
    days          = models.DecimalField(
        max_digits=5, decimal_places=1,
        verbose_name=_("Days (+/-)"),
        help_text=_("Positive = add, Negative = deduct")
    )
    justification = models.TextField(verbose_name=_("Justification"))

    class Meta:
        db_table = "hris_leave_balance_adjustments"
        verbose_name = _("Leave Balance Adjustment")
        verbose_name_plural = _("Leave Balance Adjustments")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.balance.employee} | {self.days:+} days | {self.created_at.date()}"