from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel, SoftDeleteModel

class KPI(TimeStampedModel, SoftDeleteModel):
    title = models.CharField(max_length=255, verbose_name=_("KPI Title"))
    description = models.TextField(blank=True, null=True)
    target_value = models.IntegerField(help_text=_("Target score (e.g., 0-100)"))

    class Meta:
        db_table = "hris_performance_kpis"

class EmployeeReview(TimeStampedModel, SoftDeleteModel):
    employee = models.ForeignKey("hris_core.Employee", on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey("hris_core.Employee", on_delete=models.SET_NULL, null=True, related_name="given_reviews")
    review_date = models.DateField()
    score = models.DecimalField(max_digits=5, decimal_places=2) # Masalan: 4.5
    comments = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "hris_performance_reviews"