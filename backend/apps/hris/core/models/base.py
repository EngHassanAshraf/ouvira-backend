from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel, SoftDeleteModel
from apps.company.models import Company

class Location(TimeStampedModel, SoftDeleteModel):
    """
    Kompaniya filiallari yoki ofis manzillari (Riyadh Office, Jeddah Branch va h.k.)
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="hris_locations"
    )
    name = models.CharField(max_length=255, verbose_name=_("Location Name"))
    address = models.TextField(blank=True, null=True, verbose_name=_("Address"))
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("City"))
    country = models.CharField(max_length=100, default="Saudi Arabia", verbose_name=_("Country"))

    class Meta:
        db_table = "hris_locations"
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")

    def __str__(self):
        return f"{self.name} - {self.company.name}"