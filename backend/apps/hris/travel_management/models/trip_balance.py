from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class BusinessTripBalance(TimeStampedModel):
    """
    Xodimning yillik xizmat safari balansi.
    Aniq limit yo'q — faqat yil davomida tracking.
    HR tomonidan adjustment orqali total_days belgilanadi.

    Employee's annual business trip balance.
    No fixed limit — only tracked throughout the year.
    total_days is set by HR through adjustments.
    """

    employee   = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="business_trip_balances",
        verbose_name=_("Employee")
    )
    year       = models.PositiveIntegerField(
        verbose_name=_("Year")
    )
    total_days = models.DecimalField(
        max_digits=5, decimal_places=1,
        default=0,
        verbose_name=_("Total Days"),
        help_text=_("Set by HR through adjustments")
    )
    used_days  = models.DecimalField(
        max_digits=5, decimal_places=1,
        default=0,
        verbose_name=_("Used Days"),
        help_text=_("Auto updated when trip request is approved")
    )
    company_id = models.PositiveIntegerField(
        verbose_name=_("Company ID"),
        help_text=_("Taken from request.tenant.id — multi-tenant support")
    )

    class Meta:
        db_table = "hris_business_trip_balances"
        verbose_name = _("Business Trip Balance")
        verbose_name_plural = _("Business Trip Balances")
        unique_together = (("employee", "year"),)
        indexes = [
            models.Index(fields=["employee", "year"]),
            models.Index(fields=["company_id"]),
        ]

    def __str__(self):
        return f"{self.employee} | {self.year} | {self.remaining_days} days remaining"

    @property
    def remaining_days(self):
        """Qolgan kunlar: Total - Used"""
        return self.total_days - self.used_days