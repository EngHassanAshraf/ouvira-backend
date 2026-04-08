import logging
from django.db import transaction
from django.utils import timezone
from apps.audit.services.activity_log_service import ActivityLogService
from apps.audit.utils import get_or_create_date_dim
from ...models import JobOffer, JobApplication
from ...integration.hris_core_connector import HRISCoreConnector, EmployeeCreateDTO

logger = logging.getLogger(__name__)


class JobOfferService:
    """
    Application Service for managing Job Offers and the Final Hiring Decision.

    This service does NOT import anything from hris_core directly.
    Cross-module communication is delegated to the integration layer
    (HRISCoreConnector), enforcing strict module boundaries.
    """

    @staticmethod
    @transaction.atomic
    def create_offer(application_id, offer_data):
        """Creates a draft Job Offer for a candidate."""
        application = JobApplication.objects.get(id=application_id)

        offer = JobOffer.objects.create(
            application=application,
            salary=offer_data.get('salary'),
            allowance=offer_data.get('allowance', 0.0),
            benefits=offer_data.get('benefits', ''),
            start_date=offer_data.get('start_date'),
            status=JobOffer.OfferStatus.DRAFT,
        )

        return offer

    @staticmethod
    @transaction.atomic
    def accept_offer(offer_id, user, employee_data):
        """
        Finalises the hiring process by:
          1. Accepting the offer and updating application status to HIRED.
          2. Delegating Employee creation to the HRISCoreConnector (integration layer).
          3. Logging the activity with the newly created employee_id.
        """
        offer = JobOffer.objects.select_for_update().get(id=offer_id)
        candidate = offer.application.candidate

        if offer.status == JobOffer.OfferStatus.ACCEPTED:
            return offer

        # 1. Update offer and application status
        offer.status = JobOffer.OfferStatus.ACCEPTED
        offer.responded_at = timezone.now()
        offer.save()

        application = offer.application
        application.status = JobApplication.AppStatus.HIRED
        application.save()

        # 2. Bridge to hris_core via the Integration Layer (NOT a direct import)
        dto = EmployeeCreateDTO(
            employee_id=employee_data.get('employee_id'),
            national_id=employee_data.get('national_id'),
            first_name=candidate.first_name,
            last_name=candidate.last_name,
            company_id=candidate.company_id,
            department_id=application.job_advertisement.hiring_request.department_id,
            personal_email=candidate.email,
            contact_number=candidate.phone,
            gender=employee_data.get('gender'),
            date_of_birth=employee_data.get('date_of_birth'),
        )
        new_employee_id = HRISCoreConnector.create_employee(dto)

        # 3. Audit log
        ActivityLogService.log_activity(
            user=user,
            company=candidate.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="JobOffer",
            entity_id=offer.id,
            action="OFFER_ACCEPTED_AND_HIRED",
            new_values={
                "employee_id": employee_data.get('employee_id'),
                "hris_core_employee_pk": new_employee_id,
            },
        )

        return offer

    @staticmethod
    @transaction.atomic
    def decline_offer(offer_id, user, reason=None):
        """Declines the job offer and marks the application as rejected."""
        offer = JobOffer.objects.select_for_update().get(id=offer_id)
        offer.status = JobOffer.OfferStatus.DECLINED
        offer.responded_at = timezone.now()
        offer.note = reason
        offer.save()

        application = offer.application
        application.status = JobApplication.AppStatus.REJECTED
        application.save()

        ActivityLogService.log_activity(
            user=user,
            company=offer.application.candidate.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="JobOffer",
            entity_id=offer.id,
            action="OFFER_DECLINED",
            new_values={"reason": reason},
        )

        return offer
