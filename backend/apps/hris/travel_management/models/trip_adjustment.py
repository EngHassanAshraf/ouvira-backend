from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from .trip_balance import BusinessTripBalance


class BusinessTripBalanceAdjustment(TimeStampedModel):
    """
    HR tomonidan xodim balansiga qo'lda kiritilgan o'zgarishlar tarixi.
    Har bir +/- operatsiya alohida yoziladi (delta display uchun).

    History of manual balance adjustments made by HR.
    Each +/- operation is recorded separately (for delta display).
    """

    class AdjustmentTypeChoice(models.TextChoices):
        ADD    = "add",    _("Add")
        DEDUCT = "deduct", _("Deduct")

    balance  = models.ForeignKey(
        BusinessTripBalance,
        on_delete=models.CASCADE,
        related_name="adjustments",
        verbose_name=_("Balance")
    )
    performed_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        related_name="business_trip_adjustments_made",
        verbose_name=_("Performed By")
    )
    adjustment_type = models.CharField(
        max_length=10,
        choices=AdjustmentTypeChoice.choices,
        verbose_name=_("Adjustment Type")
    )
    days = models.DecimalField(
        max_digits=5, decimal_places=1,
        verbose_name=_("Days"),
        help_text=_("Delta value — always positive, direction set by adjustment_type")
    )
    reason       = models.TextField(
        blank=True, null=True,
        verbose_name=_("Reason")
    )
    company_id   = models.PositiveIntegerField(
        verbose_name=_("Company ID"),
        help_text=_("Taken from request.tenant.id — multi-tenant support")
    )

    class Meta:
        db_table = "hris_business_trip_balance_adjustments"
        verbose_name = _("Business Trip Balance Adjustment")
        verbose_name_plural = _("Business Trip Balance Adjustments")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["balance"]),
            models.Index(fields=["company_id"]),
        ]

    def __str__(self):
        sign = "+" if self.adjustment_type == self.AdjustmentTypeChoice.ADD else "-"
        return f"{self.balance.employee} | {sign}{self.days} days | {self.created_at.date()}"
