from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel, SoftDeleteModel


class LeaveType(TimeStampedModel, SoftDeleteModel):
    """
        Ta'til turlari — KSA Mehnat Qonuniga asosan belgilangan.
        Types of leave are determined by the KSA Labor Law.
    """

    class CodeChoice(models.TextChoices):
        ANNUAL       = "annual",       _("Annual Leave")
        SICK         = "sick",         _("Sick Leave")
        NATIONAL_DAY = "national_day", _("National Day")
        EID_FITR     = "eid_fitr",     _("Eid Al-Fitr Leave")
        EID_ADHA     = "eid_adha",     _("Eid Al-Adha Leave")
        HAJJ         = "hajj",         _("Hajj Leave")
        MATERNITY    = "maternity",    _("Maternity Leave")
        PATERNITY    = "paternity",    _("Paternity Leave")
        BEREAVEMENT  = "bereavement",  _("Bereavement Leave")
        WORK_INJURY  = "work_injury",  _("Work Injury Leave")
        EXCEPTIONAL  = "exceptional",  _("Exceptional Leave")

    name          = models.CharField(max_length=100, verbose_name=_("Leave Type Name"))
    code          = models.SlugField(max_length=20, unique=True, choices=CodeChoice.choices)
    days_per_year = models.IntegerField(default=0, verbose_name=_("Default Days Per Year"))
    is_active     = models.BooleanField(default=True)

    class Meta:
        db_table = "hris_leave_types"
        verbose_name = _("Leave Type")
        verbose_name_plural = _("Leave Types")

    def __str__(self):
        return self.name