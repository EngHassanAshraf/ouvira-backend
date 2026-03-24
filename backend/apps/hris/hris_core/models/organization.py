from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel, SoftDeleteModel
from apps.company.models import Company


class JobTitle(TimeStampedModel, SoftDeleteModel):
    """
    Lavozim nomlari (Backend Developer, HR Manager, Accountant)
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="job_titles")
    title = models.CharField(max_length=255, verbose_name=_("Job Title"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))

    class Meta:
        db_table = "hris_job_titles"
        verbose_name = _("Job Title")
        verbose_name_plural = _("Job Titles")

    def __str__(self):
        return f"{self.title}"


class Department(TimeStampedModel, SoftDeleteModel):
    """
    Bo'limlar (IT, HR, Finance).
    Parent_department orqali sub-bo'limlar zanjiri yaratish mumkin.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=255, verbose_name=_("Department Name"))
    parent_department = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sub_departments"
    )
    # Manager xodim bo'ladi, buni string orqali bog'laymiz
    manager = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments"
    )

    class Meta:
        db_table = "hris_departments"
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class Position(TimeStampedModel, SoftDeleteModel):
    """
    Vakansiya o'rni: Bo'lim + Lavozim + Lokatsiya birlashmasi.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="positions")
    job_title = models.ForeignKey(JobTitle, on_delete=models.PROTECT, related_name="positions")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="positions")
    location = models.ForeignKey("hris_core.Location", on_delete=models.PROTECT, related_name="positions")

    # Position iyerarxiyasi (Kim kimga bo'ysunadi)
    reports_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direct_reports"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "hris_positions"
        verbose_name = _("Position")
        verbose_name_plural = _("Positions")

    def __str__(self):
        return f"{self.job_title.title} in {self.department.name}"