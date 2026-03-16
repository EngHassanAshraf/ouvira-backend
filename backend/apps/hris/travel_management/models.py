from django.db import models
from apps.core.models import TimeStampedModel, SoftDeleteModel

class TravelRequest(TimeStampedModel, SoftDeleteModel):
    employee = models.ForeignKey("hris_core.Employee", on_delete=models.CASCADE)
    destination = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    purpose = models.TextField()
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "hris_travel_requests"