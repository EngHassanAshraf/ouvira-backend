"""
InternalAuthAuditService
========================
Records every internal login attempt to InternalLoginAttempt.
Runs synchronously inside the request cycle — kept lightweight
(single INSERT, no external calls).
"""
import logging
from typing import Optional

from ..models import InternalLoginAttempt

logger = logging.getLogger(__name__)


class InternalAuthAuditService:

    @staticmethod
    def record(
        identifier: str,
        outcome: str,
        failure_reason: str = "",
        user=None,
        company_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: str = "",
    ) -> None:
        """
        Persist a login attempt record.

        Args:
            identifier:     Email or username submitted.
            outcome:        "success" | "failure" | "locked"
            failure_reason: Short machine-readable reason (e.g. "bad_password").
            user:           CustomUser instance if resolved, else None.
            company_id:     Resolved company ID if available.
            ip_address:     Client IP.
            user_agent:     HTTP User-Agent header.
        """
        try:
            InternalLoginAttempt.objects.create(
                user=user,
                identifier=identifier,
                company_id=company_id,
                outcome=outcome,
                failure_reason=failure_reason,
                ip_address=ip_address,
                user_agent=user_agent or "",
            )
        except Exception:
            # Audit failure must never break the login flow
            logger.exception(
                "InternalAuthAuditService: failed to record attempt for identifier=<redacted>"
            )
