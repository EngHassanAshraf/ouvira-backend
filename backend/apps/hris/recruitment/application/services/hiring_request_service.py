import logging
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.audit.services.activity_log_service import ActivityLogService
from apps.audit.utils import get_or_create_date_dim
from ...models import HiringRequest, HiringRequestApproval
from ...domain.events.dispatcher import dispatcher
from ...domain.events.events import (
    HiringRequestSubmitted,
    HiringRequestApproved,
    HiringRequestRejected
)

logger = logging.getLogger(__name__)
User = get_user_model()

# Fields that are safe to update on a HiringRequest
_EDITABLE_FIELDS = {"job_title", "department", "vacancies", "purpose"}


class HiringRequestService:
    """
    Application Service for orchestrating Hiring Request workflows.
    Follows DDD principles by keeping domain logic and side effects (logging, events) here.
    """

    @staticmethod
    @transaction.atomic
    def create_hiring_request(user, company, data):
        """Creates a new Hiring Request in DRAFT state."""
        hiring_request = HiringRequest.objects.create(
            company=company,
            created_by=user,
            job_title=data.get("job_title"),
            department=data.get("department"),
            vacancies=data.get("vacancies", 1),
            purpose=data.get("purpose", ""),
            status=HiringRequest.Status.DRAFT
        )

        ActivityLogService.log_activity(
            user=user,
            company=company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="HiringRequest",
            entity_id=hiring_request.id,
            action="CREATED",
            new_values={
                "job_title_id": hiring_request.job_title_id,
                "department_id": hiring_request.department_id,
                "vacancies": hiring_request.vacancies,
                "purpose": hiring_request.purpose,
                "status": hiring_request.status,
            }
        )

        return hiring_request

    @staticmethod
    @transaction.atomic
    def update_hiring_request(request_id: int, user, data: dict) -> HiringRequest:
        """
        Updates a Hiring Request.

        Rules:
        - Only DRAFT requests can be edited.
        - Only whitelisted fields are accepted (job_title, department, vacancies, purpose).
        - Logs old vs new values for audit trail.
        """
        hiring_request = HiringRequest.objects.select_for_update().get(id=request_id)

        if hiring_request.status != HiringRequest.Status.DRAFT:
            raise ValueError(
                f"Cannot edit a hiring request in '{hiring_request.status}' status. "
                "Only draft requests can be modified."
            )

        old_values = {
            "job_title_id": hiring_request.job_title_id,
            "department_id": hiring_request.department_id,
            "vacancies": hiring_request.vacancies,
            "purpose": hiring_request.purpose,
        }

        changed = False
        for field, value in data.items():
            if field not in _EDITABLE_FIELDS:
                continue
            if getattr(hiring_request, field) != value:
                setattr(hiring_request, field, value)
                changed = True

        if changed:
            hiring_request.save()
            ActivityLogService.log_activity(
                user=user,
                company=hiring_request.company,
                date_dim=get_or_create_date_dim(timezone.now().date()),
                entity_type="HiringRequest",
                entity_id=hiring_request.id,
                action="UPDATED",
                old_values=old_values,
                new_values={
                    "job_title_id": hiring_request.job_title_id,
                    "department_id": hiring_request.department_id,
                    "vacancies": hiring_request.vacancies,
                    "purpose": hiring_request.purpose,
                }
            )

        return hiring_request

    @staticmethod
    @transaction.atomic
    def cancel_hiring_request(request_id: int, user, reason: str = "") -> HiringRequest:
        """
        Cancels a Hiring Request.

        Rules:
        - DRAFT and SUBMITTED requests can be cancelled.
        - APPROVED and already REJECTED requests cannot be cancelled.
        - Cancellation is a terminal state — it cannot be undone.
        """
        hiring_request = HiringRequest.objects.select_for_update().get(id=request_id)

        cancellable = {HiringRequest.Status.DRAFT, HiringRequest.Status.SUBMITTED}
        if hiring_request.status not in cancellable:
            raise ValueError(
                f"Cannot cancel a hiring request in '{hiring_request.status}' status. "
                "Only draft or submitted requests can be cancelled."
            )

        old_status = hiring_request.status
        hiring_request.status = HiringRequest.Status.REJECTED  # reuse REJECTED as cancelled
        hiring_request.save()

        # Mark any pending approvals as rejected
        HiringRequestApproval.objects.filter(
            hiring_request=hiring_request,
            status=HiringRequestApproval.ApprovalStatus.PENDING
        ).update(
            status=HiringRequestApproval.ApprovalStatus.REJECTED,
            note=reason or "Cancelled by requester.",
            action_at=timezone.now(),
        )

        ActivityLogService.log_activity(
            user=user,
            company=hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="HiringRequest",
            entity_id=hiring_request.id,
            action="CANCELLED",
            old_values={"status": old_status},
            new_values={"status": hiring_request.status, "reason": reason}
        )

        return hiring_request

    @staticmethod
    @transaction.atomic
    def soft_delete_hiring_request(request_id: int, user) -> None:
        """
        Soft-deletes a Hiring Request.

        Rules:
        - Only DRAFT requests can be deleted.
        - Submitted/approved requests must be cancelled first.
        """
        hiring_request = HiringRequest.objects.select_for_update().get(id=request_id)

        if hiring_request.status != HiringRequest.Status.DRAFT:
            raise ValueError(
                f"Cannot delete a hiring request in '{hiring_request.status}' status. "
                "Cancel it first, or only draft requests can be deleted."
            )

        hiring_request.is_deleted = True
        hiring_request.deleted_at = timezone.now()
        hiring_request.save(update_fields=["is_deleted", "deleted_at"])

        ActivityLogService.log_activity(
            user=user,
            company=hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="HiringRequest",
            entity_id=hiring_request.id,
            action="DELETED"
        )

    @staticmethod
    @transaction.atomic
    def submit_hiring_request(request_id, user):
        """Submits a hiring request for approval."""
        hiring_request = HiringRequest.objects.select_for_update().get(id=request_id)

        if hiring_request.status != HiringRequest.Status.DRAFT:
            raise ValueError("Only draft requests can be submitted.")

        hiring_request.status = HiringRequest.Status.SUBMITTED
        hiring_request.save()

        approval_steps = [
            HiringRequestApproval.ApproverRole.EMPLOYEE,
            HiringRequestApproval.ApproverRole.HR,
            HiringRequestApproval.ApproverRole.MANAGER
        ]

        for role in approval_steps:
            HiringRequestApproval.objects.create(
                hiring_request=hiring_request,
                role_type=role,
                status=HiringRequestApproval.ApprovalStatus.PENDING
            )

        ActivityLogService.log_activity(
            user=user,
            company=hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="HiringRequest",
            entity_id=hiring_request.id,
            action="SUBMITTED"
        )

        dispatcher.dispatch(HiringRequestSubmitted(
            request_id=hiring_request.id,
            company_id=hiring_request.company.id,
            submitted_by_id=user.id
        ))

        return hiring_request

    @staticmethod
    @transaction.atomic
    def approve_request(request_id, user, role_type, note=None):
        """Approves a specific step in the hiring request."""
        hiring_request = HiringRequest.objects.select_for_update().get(id=request_id)
        approval = HiringRequestApproval.objects.get(
            hiring_request=hiring_request,
            role_type=role_type,
            status=HiringRequestApproval.ApprovalStatus.PENDING
        )

        approval.status = HiringRequestApproval.ApprovalStatus.APPROVED
        approval.approver = user
        approval.note = note
        approval.action_at = timezone.now()
        approval.save()

        ActivityLogService.log_activity(
            user=user,
            company=hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="HiringRequest",
            entity_id=hiring_request.id,
            action=f"APPROVED_{role_type.upper()}"
        )

        if not HiringRequestApproval.objects.filter(
            hiring_request=hiring_request,
            status=HiringRequestApproval.ApprovalStatus.PENDING
        ).exists():
            hiring_request.status = HiringRequest.Status.APPROVED
            hiring_request.save()

            dispatcher.dispatch(HiringRequestApproved(
                request_id=hiring_request.id,
                company_id=hiring_request.company.id,
                approved_by_id=user.id
            ))

        return hiring_request

    @staticmethod
    @transaction.atomic
    def reject_request(request_id, user, role_type, reason):
        """Rejects the hiring request at any step."""
        hiring_request = HiringRequest.objects.select_for_update().get(id=request_id)

        approval = HiringRequestApproval.objects.get(
            hiring_request=hiring_request,
            role_type=role_type,
            status=HiringRequestApproval.ApprovalStatus.PENDING
        )
        approval.status = HiringRequestApproval.ApprovalStatus.REJECTED
        approval.approver = user
        approval.note = reason
        approval.action_at = timezone.now()
        approval.save()

        hiring_request.status = HiringRequest.Status.REJECTED
        hiring_request.save()

        ActivityLogService.log_activity(
            user=user,
            company=hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="HiringRequest",
            entity_id=hiring_request.id,
            action=f"REJECTED_{role_type.upper()}",
            new_values={"reason": reason}
        )

        dispatcher.dispatch(HiringRequestRejected(
            request_id=hiring_request.id,
            company_id=hiring_request.company.id,
            rejected_by_id=user.id,
            reason=reason
        ))

        return hiring_request
