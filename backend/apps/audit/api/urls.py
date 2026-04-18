from django.urls import path

from .views import (
    NotificationListView,
    NotificationMarkReadView,
    ActivityLogListView,
    EmployeeActivityLogListView,
    ActivityLogDetailView,
    SecurityAuditLogListView,
)

app_name = "audit"

urlpatterns = [
    # Notifications
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/mark-read/", NotificationMarkReadView.as_view(), name="notification-mark-read"),

    # Activity logs
    path("activity-logs/", ActivityLogListView.as_view(), name="activity-log-list"),
    path("activity-logs/my/", ActivityLogDetailView.as_view(), name="activity-log-my"),
    path("activity-logs/employees/<int:employee_pk>/", EmployeeActivityLogListView.as_view(), name="employee-activity-log"),

    # Security audit logs
    path("security-logs/", SecurityAuditLogListView.as_view(), name="security-log-list"),
]
