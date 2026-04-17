from django.db import models
from django.utils.translation import gettext_lazy as _

from django.conf import settings
from apps.core.models import TimeStampedModel, SoftDeleteModel


class Company(TimeStampedModel, SoftDeleteModel):
    parent_company = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="subsidiaries",
        blank=True,
        null=True,
    )
    is_parent_company = models.BooleanField(default=False)

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        DEACTIVATED = "deactivated", _("Deactivated")
        DELETED = "deleted", _("Deleted")

    name = models.CharField(max_length=255, unique=True, verbose_name=_("Company Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    logo = models.ImageField(
        upload_to="companies/logo",
        null=True,
        blank=True,
        verbose_name=_("Company Logo"),
    )
    address = models.TextField(null=True, blank=True, verbose_name=_("Company Address"))
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name=_("Status"),
    )
    create_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_companies",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "companies"
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class CompanySettings(models.Model):
    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name="settings"
    )
    default_language = models.CharField(max_length=20)
    default_currency = models.CharField(max_length=10)
    timezone = models.CharField(max_length=50)
    fiscal_year_start_month = models.IntegerField()
    feature_flags = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.company.name} settings"

    class Meta:
        verbose_name = _("Company Settings")
        verbose_name_plural = _("Companies Settings")
