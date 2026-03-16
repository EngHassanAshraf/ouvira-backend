from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.core.models import TimeStampedModel, SoftDeleteModel
from apps.company.models import Company


class Employee(TimeStampedModel, SoftDeleteModel):
    class GenderChoice(models.TextChoices):
        MALE = "M", _("Male")
        FEMALE = "F", _("Female")

    class MaritalStatusChoice(models.TextChoices):
        SINGLE = "S", _("Single")
        MARRIED = "M", _("Married")
        DIVORCED = "D", _("Divorced")
        WIDOWED = "W", _("Widowed")

    # Hassan yozgan bazaviy ulanishlar
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_profile",
        blank=True,
        null=True,
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="employees")

    # Asosiy ma'lumotlar
    employee_id = models.CharField(max_length=50, verbose_name=_("Employee ID"))  # Masalan: EMP-001
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=100, verbose_name=_("Last Name"))

    # KSA Business Requirements (Saudiya talablari)
    national_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("National ID / IQAMA"),
        help_text=_("10 digits for KSA nationals or residents")
    )
    passport_number = models.CharField(max_length=20, blank=True, null=True)
    nationality = models.CharField(max_length=100, default="Saudi Arabian")

    # Shaxsiy ma'lumotlar
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GenderChoice.choices, blank=True, null=True)
    marital_status = models.CharField(max_length=1, choices=MaritalStatusChoice.choices, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    personal_email = models.EmailField(blank=True, null=True)

    class Meta:
        db_table = "hris_employees"
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")
        unique_together = (("company", "employee_id"),)
        indexes = [
            models.Index(fields=["company", "employee_id"]),
            models.Index(fields=["national_id"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"