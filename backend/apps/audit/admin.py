# user_activity/admin_enhanced.py
from django.contrib import admin
from .models import ActivityLog, Notification, DateDim, SecurityAuditLog
# from apps.identity.account.models.user import RoleChangeLog

admin.site.register(DateDim)
admin.site.register(SecurityAuditLog)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "company",
        "date",
        "ip_address",
        "entity_type",
        "entity_id",
        "action",
        "old_values",
        "new_values",
    )
    list_filter = ("action", "created_at")
    search_fields = ("user__username", "ip_address")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "read", "created_at")
    list_filter = ("read", "created_at")
    search_fields = ("user__username", "message")


# @admin.register(RoleChangeLog)
# class RoleChangeLogAdmin(admin.ModelAdmin):
#     list_display = ("user", "old_role", "new_role", "changed_by", "timestamp")
#     list_filter = ("old_role", "new_role", "timestamp")
#     search_fields = ("user__username", "changed_by__username")
