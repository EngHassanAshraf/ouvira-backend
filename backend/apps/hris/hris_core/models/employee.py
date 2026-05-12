from django.db import models
from django.utils.translation import gettext_lazy as _
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

    class NationalIDStatusChoice(models.TextChoices):
        ACTIVE = "active", _("Active")
        EXPIRED = "expired", _("Expired")
        PENDING = "pending", _("Pending")

    class IqamaStatusChoice(models.TextChoices):
        ACTIVE = "active", _("Active")
        EXPIRED = "expired", _("Expired")
        PENDING = "pending", _("Pending")
        NOT_APPLICABLE = "not_applicable", _("Not Applicable")

    # User account reference
    user_id = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("User ID"),
        help_text=_("Reference to the shared user account"),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    department = models.ForeignKey(
        "hris_core.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        verbose_name=_("Department"),
    )
    location = models.ForeignKey(
        "hris_core.Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        verbose_name=_("Work Location"),
    )
    # Reporting manager — self-referential FK
    reporting_manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direct_reports",
        verbose_name=_("Reporting Manager"),
    )

    # Core identifiers
    employee_id = models.CharField(max_length=50, verbose_name=_("Employee ID"))
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=100, verbose_name=_("Last Name"))

    # KSA identity fields
    national_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("National ID / IQAMA"),
        help_text=_("10 digits for KSA nationals or residents"),
    )
    national_id_job_title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Job Title on National ID"),
    )
    national_id_status = models.CharField(
        max_length=20,
        choices=NationalIDStatusChoice.choices,
        blank=True,
        null=True,
        verbose_name=_("National ID Status"),
    )
    passport_number = models.CharField(max_length=20, blank=True, null=True)
    visa_number = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_("Visa Number")
    )
    iqama_status = models.CharField(
        max_length=20,
        choices=IqamaStatusChoice.choices,
        blank=True,
        null=True,
        verbose_name=_("Residency Permit Status (Iqama)"),
    )
    fingerprint_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Fingerprint ID")
    )
    nationality = models.CharField(max_length=100, default="Saudi Arabian")

    # Personal details
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=1, choices=GenderChoice.choices, blank=True, null=True
    )
    marital_status = models.CharField(
        max_length=1, choices=MaritalStatusChoice.choices, blank=True, null=True
    )
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    secondary_phone = models.CharField(
        max_length=20, blank=True, null=True, verbose_name=_("Secondary Phone")
    )
    personal_email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True, verbose_name=_("Address"))

    # Photo
    photo = models.ImageField(
        upload_to="employees/photos/",
        blank=True,
        null=True,
        verbose_name=_("Profile Photo"),
    )

    # Job title (direct FK for Figma "job title" field in Job Details tab)
    job_title = models.ForeignKey(
        "hris_core.JobTitle",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        verbose_name=_("Job Title"),
    )

    # Work email (system/company email — distinct from personal_email)
    work_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_("Work Email"),
        help_text=_("Company/system email address used for login"),
    )

    # System user flag
    is_system_user = models.BooleanField(
        default=False, verbose_name=_("Active System User")
    )

    class Meta:
        db_table = "hris_employees"
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")
        unique_together = (("company", "employee_id"),)
        indexes = [
            models.Index(fields=["company", "employee_id"]),
            models.Index(fields=["national_id"]),
            models.Index(fields=["company", "is_deleted"]),
            models.Index(fields=["nationality"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def employee_status(self):
        """Derive current status from the latest active Employment record."""
        latest = (
            self.employments.filter(is_deleted=False)
            .order_by("-created_at")
            .first()
        )
        if latest:
            return latest.status
        return None

    @property
    def user(self):
        if self.user_id is None:
            return None
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            return User.objects.get(pk=self.user_id)
        except User.DoesNotExist:
            return None

    @user.setter
    def user(self, user_obj):
        self.user_id = user_obj.pk if user_obj else None
