"""
RecruitmentAuditService — thin wrapper around ActivityLogService
scoped to recruitment entity types.
"""
import logging
from datetime import date

from apps.audit.services.activity_log_service import ActivityLogService
from apps.audit.utils import get_or_create_date_dim

logger = logging.getLogger(__name__)


class RecruitmentAuditService:
    """
    Logs recruitment-specific actions to the shared ActivityLog.

    entity_type values:
        "hiring_request" | "job_advertisement" | "application"

    action values (per entity):
        hiring_request:    submitted, approved, rejected, cancelled, deleted
        job_advertisement: published, saved_as_draft, closed, reopened
        application:       added, updated, classification_changed, stage_moved
    """

    @staticmethod
    def log(
        user,
        company,
        entity_type: str,
        entity_id: int,
        action: str,
        entity_label: str = "",
        details: dict = None,
        ip_address: str = None,
    ) -> None:
        """
        Log a recruitment action. Silently swallows errors so audit
        failures never break the main operation.
        """
        try:
            date_dim = get_or_create_date_dim(date.today())
            ActivityLogService.log_activity(
                user=user,
                company=company,
                date_dim=date_dim,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                new_values={"label": entity_label, **(details or {})},
                ip_address=ip_address,
            )
        except Exception as exc:
            logger.warning(
                "RecruitmentAuditService.log failed silently: %s", exc
            )
