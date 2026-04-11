import logging
from django.db import transaction
from django.utils import timezone
from apps.audit.services.activity_log_service import ActivityLogService
from apps.audit.utils import get_or_create_date_dim
from ...models import Candidate, JobApplication, JobAdvertisement
from .recruitment_audit_service import RecruitmentAuditService

logger = logging.getLogger(__name__)

class ApplicationService:
    """
    Service for managing Job Applications and Candidate lifecycles.
    """

    @staticmethod
    @transaction.atomic
    def apply_for_job(advertisement_id, candidate_data, company_id):
        """
        Registers a new candidate and their application for a specific job.
        Used for internal/external talent sourcing.
        """
        ad = JobAdvertisement.objects.get(id=advertisement_id)
        
        # 1. Get or Create Candidate (Idempotency by email)
        candidate, created = Candidate.objects.get_or_create(
            email=candidate_data.get('email'),
            defaults={
                'first_name': candidate_data.get('first_name'),
                'last_name': candidate_data.get('last_name'),
                'phone': candidate_data.get('phone'),
                'linkedin_url': candidate_data.get('linkedin_url'),
                'source': candidate_data.get('source', 'Direct'),
                'company_id': company_id
            }
        )

        # 2. Create Application
        application, app_created = JobApplication.objects.get_or_create(
            candidate=candidate,
            job_advertisement=ad,
            defaults={
                'status': JobApplication.AppStatus.APPLIED,
                'classification': JobApplication.Classification.NONE
            }
        )

        if not app_created:
            logger.info(f"Candidate {candidate.email} already applied for job {ad.title}")
            return application

        # 3. Log Activity
        ActivityLogService.log_activity(
            user=None,  # External action
            company=ad.hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="JobApplication",
            entity_id=application.id,
            action="APPLIED",
            new_values={k: str(v) if hasattr(v, 'id') else v for k, v in candidate_data.items()} if candidate_data else {}
        )

        return application

    @staticmethod
    @transaction.atomic
    def move_to_stage(application_id, new_status, user, classification=None):
        """
        Moves an application through the recruitment pipeline (Kanban stages).
        """
        application = JobApplication.objects.select_for_update().get(id=application_id)
        old_status = application.status
        
        application.status = new_status
        if classification:
            application.classification = classification
        
        application.save()

        # Log Activity
        ActivityLogService.log_activity(
            user=user,
            company=application.job_advertisement.hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="JobApplication",
            entity_id=application.id,
            action=f"STAGE_CHANGED_TO_{new_status.upper()}",
            old_values={"status": old_status},
            new_values={"status": new_status, "classification": classification}
        )

        RecruitmentAuditService.log(
            user=user,
            company=application.job_advertisement.hiring_request.company,
            entity_type="application",
            entity_id=application.pk,
            action="stage_moved",
            entity_label=f"{application.candidate} — {application.job_advertisement.title}",
            details={"from_status": old_status, "to_status": new_status},
        )

        return application
