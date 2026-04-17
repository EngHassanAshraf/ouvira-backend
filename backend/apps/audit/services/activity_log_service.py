"""
Activity Log Service — business logic for activity log operations.
"""
import logging
from django.db.models import QuerySet

from ..models import ActivityLog

logger = logging.getLogger(__name__)


class ActivityLogService:
    """Service for activity log operations."""

    @staticmethod
    def get_activity_logs_for_company(company_id: int) -> QuerySet:
        """Get activity logs for a company, newest first."""
        return ActivityLog.objects.filter(
            company_id=company_id,
        ).select_related("user", "date").order_by("-created_at")

    @staticmethod
    def get_activity_logs_for_user(user) -> QuerySet:
        """Get activity logs for a specific user."""
        return ActivityLog.objects.filter(
            user=user,
        ).select_related("company", "date").order_by("-created_at")

    @staticmethod
    def _sanitize_data(data):
        """Recursively convert model instances to IDs for JSON serialization."""
        if isinstance(data, dict):
            return {k: ActivityLogService._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [ActivityLogService._sanitize_data(v) for v in data]
        elif hasattr(data, "pk"):
            return data.pk
        return data

    @staticmethod
    def log_activity(
        user,
        company_id: int,
        date_dim,
        entity_type: str,
        entity_id: int,
        action: str,
        old_values: dict = None,
        new_values: dict = None,
        ip_address: str = None,
    ) -> ActivityLog:
        """
        Log an activity.

        Accepts ``company_id`` (int) instead of a Company instance so that
        callers inside signals don't need to fetch the full object.
        """
        safe_old = ActivityLogService._sanitize_data(old_values)
        safe_new = ActivityLogService._sanitize_data(new_values)

        log = ActivityLog.objects.create(
            user=user,
            company_id=company_id,
            date=date_dim,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_values=safe_old,
            new_values=safe_new,
            ip_address=ip_address,
        )
        logger.info(
            "Activity logged: %s by %s on %s:%s", action, user, entity_type, entity_id
        )
        return log
