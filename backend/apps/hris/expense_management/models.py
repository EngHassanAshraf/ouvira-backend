from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel, SoftDeleteModel

class ExpenseClaim(TimeStampedModel, SoftDeleteModel):
    class StatusChoice(models.TextChoices):
        DRAFT = "draft", _("Draft")
        SUBMITTED = "submitted", _("Submitted")
        PAID = "paid", _("Paid")

    employee = models.ForeignKey("hris_core.Employee", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="SAR") # Saudi Riyal default
    status = models.CharField(max_length=20, choices=StatusChoice.choices, default=StatusChoice.DRAFT)
    attachment = models.FileField(upload_to="expenses/%Y/%m/", null=True, blank=True)

    class Meta:
        db_table = "hris_expense_claims"