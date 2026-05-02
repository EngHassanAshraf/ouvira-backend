from django.db import models
from django.utils.translation import gettext_lazy as _


from apps.core.models import TimeStampedModel, SoftDeleteModel


class BusinessTripBenefit(TimeStampedModel, SoftDeleteModel):
    """
    Business Trip uchun berilgan imtiyozlar (benefit).
    fixed benefits tizimi tomonidan beirlgan
    coustom benefit HR tomonidan qo'lda qo'lda qo'shiladi

    Benefits provided for business trips.
    Fixed benefits are defined by the system,
    custom benefits are added manually by HR.
    """

    class CodeChoice(models.TextChoices):
        FLIGHT_TICKET = "flight_ticket", _("Flight Ticket")
        ACCOMMODATION = "accommodation", _("Accommodation")
        FOOD          = "food",          _("Food")
        OTHER         = "other",          _("Other")


    name             = models.CharField(
        max_length=100,
        verbose_name=_("Benefit Name")
    )
    code = models.SlugField(
        max_length=50,
        choices=CodeChoice.choices,
        default=CodeChoice.OTHER,
        verbose_name=_("Benefit Code")
    )
    is_fixed = models.BooleanField(
        default=False,
        verbose_name=_("Is Fixed"),
        help_text=_("True = system-defined benefit, False = manually added by HR")
    )
    company_id = models.PositiveIntegerField(
        verbose_name=_("Company ID"),
        help_text=_("Taken from request.tenant.id  - multi-tenant support")
    )

    class Meta:
        db_table = "hris_business_trip_benefits"
        verbose_name = _("Business Trip Benefit")
        verbose_name_plural = _("Business Trip Benefits")
        unique_together = (("code", "company_id"),)

    def __str__(self):
        return self.name