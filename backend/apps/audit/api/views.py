"""
Audit views — notifications, activity logs, and security audit logs.
"""
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from ..services import NotificationService, ActivityLogService, SecurityAuditLogService
from .serializers import (
    NotificationListSerializer,
    ActivityLogListSerializer,
    ActivityLogSerializer,
    SecurityAuditLogSerializer,
)
from apps.access_control.permissions.IsAdminUser import IsAdminUser


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200


# ── Notifications ──────────────────────────────────────────────────────────────

class NotificationListView(ListAPIView):
    """GET /notifications/ — list notifications for the authenticated user."""
    serializer_class = NotificationListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = NotificationService.get_user_notifications(self.request.user)
        if self.request.query_params.get("unread", "").lower() == "true":
            qs = qs.filter(read=False)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data = {
            "unread_count": NotificationService.get_unread_count(request.user),
            "results": response.data,
        }
        return response


class NotificationMarkReadView(APIView):
    """POST /notifications/mark-read/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.data.get("all"):
            count = NotificationService.mark_all_read(request.user)
            return Response(
                {"detail": f"Marked {count} notifications as read."}, status=HTTP_200_OK
            )
        notification_id = request.data.get("notification_id")
        if notification_id:
            try:
                NotificationService.mark_as_read(notification_id, request.user)
                return Response({"detail": "Notification marked as read."}, status=HTTP_200_OK)
            except Exception:
                return Response({"detail": "Notification not found."}, status=HTTP_404_NOT_FOUND)
        return Response(
            {"detail": "Provide 'notification_id' or 'all': true."}, status=HTTP_200_OK
        )


# ── Activity Logs ──────────────────────────────────────────────────────────────

class ActivityLogListView(ListAPIView):
    """
    GET /activity-logs/
    Admin-only. Filters: ?entity_type=Employee &entity_id=<pk>
    &action=created|updated|deleted &search=<text>
    """
    serializer_class = ActivityLogListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = ActivityLogService.get_activity_logs_for_company(
            company_id=self.request.tenant.id
        )
        entity_type = self.request.query_params.get("entity_type")
        entity_id   = self.request.query_params.get("entity_id")
        action      = self.request.query_params.get("action")
        search      = self.request.query_params.get("search")

        if entity_type:
            qs = qs.filter(entity_type=entity_type)
        if entity_id:
            qs = qs.filter(entity_id=entity_id)
        if action:
            qs = qs.filter(action=action)
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(entity_type__icontains=search) | Q(action__icontains=search)
            )
        return qs


class EmployeeActivityLogListView(ListAPIView):
    """
    GET /activity-logs/employees/<employee_pk>/
    Full change history for a single employee.
    Filters: ?action=created|updated|deleted
    """
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardPagination

    def get_queryset(self):
        employee_pk = self.kwargs["employee_pk"]
        qs = ActivityLogService.get_activity_logs_for_company(
            company_id=self.request.tenant.id
        ).filter(entity_type="Employee", entity_id=employee_pk)

        action = self.request.query_params.get("action")
        if action:
            qs = qs.filter(action=action)
        return qs


class ActivityLogDetailView(ListAPIView):
    """GET /activity-logs/my/ — current user's own activity logs."""
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        return ActivityLogService.get_activity_logs_for_user(self.request.user)


# ── Security Audit Logs ────────────────────────────────────────────────────────

class SecurityAuditLogListView(ListAPIView):
    """GET /security-logs/ — current user's security audit logs."""
    serializer_class = SecurityAuditLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        return SecurityAuditLogService.get_logs_for_user(self.request.user)
