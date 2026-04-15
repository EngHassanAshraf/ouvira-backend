from django.db import models
from django.conf import settings

from apps.identity.account.models import CustomUser
from apps.company.models import Company


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification"
    )
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"


class DateDim(models.Model):
    id = models.IntegerField(primary_key=True)  # YYYYMMDD
    full_date = models.DateField(unique=True)

    day = models.IntegerField()
    day_name = models.CharField(max_length=20)
    day_of_week = models.IntegerField()
    day_of_year = models.IntegerField()

    week_of_year = models.IntegerField()
    iso_week = models.IntegerField()

    month = models.IntegerField()
    month_name = models.CharField(max_length=20)
    quarter = models.IntegerField()

    year = models.IntegerField()
    is_weekend = models.BooleanField()

    fiscal_month = models.IntegerField()
    fiscal_quarter = models.IntegerField()
    fiscal_year = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.full_date)

    class Meta:
        verbose_name = "Date Dimension"
        verbose_name_plural = "Date Dimensions"


class ActivityLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    date = models.ForeignKey(DateDim, on_delete=models.PROTECT)
    entity_type = models.CharField(max_length=100)
    entity_id = models.IntegerField()
    action = models.CharField(max_length=50)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"

    class Meta:
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"


class SecurityAuditLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    date = models.ForeignKey(DateDim, on_delete=models.PROTECT)

    action = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user} - {self.action}"

    class Meta:
        verbose_name = "Security Audit Log"
        verbose_name_plural = "Security Audit Logs"
