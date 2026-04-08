import logging
from django.db import transaction
from django.utils import timezone
from apps.audit.services.activity_log_service import ActivityLogService
from apps.audit.utils import get_or_create_date_dim
from ...models import Candidate, CandidateDocument

logger = logging.getLogger(__name__)

class DocumentService:
    """
    Service for managing Candidate Document verification.
    """

    @staticmethod
    @transaction.atomic
    def upload_document(candidate_id, doc_type, file, user):
        """
        Uploads or updates a specific document for a candidate.
        """
        candidate = Candidate.objects.get(id=candidate_id)
        
        document, created = CandidateDocument.objects.update_or_create(
            candidate=candidate,
            doc_type=doc_type,
            defaults={
                'file': file,
                'status': CandidateDocument.Status.PENDING
            }
        )

        # Log Activity
        ActivityLogService.log_activity(
            user=user,
            company=candidate.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="CandidateDocument",
            entity_id=document.id,
            action="UPLOADED",
            new_values={"doc_type": doc_type}
        )

        return document

    @staticmethod
    @transaction.atomic
    def verify_document(document_id, status, user, note=None):
        """
        Approves or rejects a candidate document.
        """
        document = CandidateDocument.objects.select_for_update().get(id=document_id)
        
        document.status = status
        document.note = note
        document.save()

        # Log Activity
        ActivityLogService.log_activity(
            user=user,
            company=document.candidate.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="CandidateDocument",
            entity_id=document.id,
            action=f"VERIFIED_{status.upper()}",
            new_values={"status": status, "note": note}
        )

        return document
