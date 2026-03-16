from django.db import models
from apps.core.models import TimeStampedModel, SoftDeleteModel

class Termination(TimeStampedModel, SoftDeleteModel):
    employee = models.OneToOneField("hris_core.Employee", on_delete=models.CASCADE)
    termination_date = models.DateField()
    reason = models.TextField()
    last_working_day = models.DateField()
    is_voluntary = models.BooleanField(default=True)

    class Meta:
        db_table = "hris_terminations"