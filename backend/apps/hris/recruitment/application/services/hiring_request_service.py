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

        # Log Activity
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
                "status": hiring_request.status
            }
        )

        return hiring_request

    @staticmethod
    @transaction.atomic
    def submit_hiring_request(request_id, user):
        """Submits a hiring request for approval."""
        hiring_request = HiringRequest.objects.select_for_update().get(id=request_id)
        
        if hiring_request.status != HiringRequest.Status.DRAFT:
            raise ValueError("Only draft requests can be submitted.")

        hiring_request.status = HiringRequest.Status.SUBMITTED
        hiring_request.save()

        # Initialize Approval Flow (As seen in UI screenshots: Employee -> HR -> Manager)
        # For now, we seed the approval steps. Actual assignment logic can be added later.
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

        # Log Activity
        ActivityLogService.log_activity(
            user=user,
            company=hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="HiringRequest",
            entity_id=hiring_request.id,
            action="SUBMITTED"
        )

        # Dispatch Domain Event
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

        # Log Activity
        ActivityLogService.log_activity(
            user=user,
            company=hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="HiringRequest",
            entity_id=hiring_request.id,
            action=f"APPROVED_{role_type.upper()}"
        )

        # Check if all steps are approved
        if not HiringRequestApproval.objects.filter(
            hiring_request=hiring_request,
            status=HiringRequestApproval.ApprovalStatus.PENDING
        ).exists():
            hiring_request.status = HiringRequest.Status.APPROVED
            hiring_request.save()
            
            # Dispatch Final Approval Event
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
        
        # Reject specific step
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

        # Update Request Status
        hiring_request.status = HiringRequest.Status.REJECTED
        hiring_request.save()

        # Log Activity
        ActivityLogService.log_activity(
            user=user,
            company=hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="HiringRequest",
            entity_id=hiring_request.id,
            action=f"REJECTED_{role_type.upper()}",
            new_values={"reason": reason}
        )

        # Dispatch Event
        dispatcher.dispatch(HiringRequestRejected(
            request_id=hiring_request.id,
            company_id=hiring_request.company.id,
            rejected_by_id=user.id,
            reason=reason
        ))

        return hiring_request
