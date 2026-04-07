import logging
from django.db import transaction
from django.utils import timezone
from apps.audit.services.activity_log_service import ActivityLogService
from apps.audit.utils import get_or_create_date_dim
from ...models import HiringRequest, JobAdvertisement

logger = logging.getLogger(__name__)

class JobAdvertisementService:
    """
    Service for managing Job Advertisements.
    """

    @staticmethod
    @transaction.atomic
    def create_from_request(request_id: int):
        """
        Creates a draft Job Advertisement from an approved Hiring Request.
        Usually triggered by a Domain Event.
        """
        hiring_request = HiringRequest.objects.get(id=request_id)
        
        if hiring_request.status != HiringRequest.Status.APPROVED:
            raise ValueError("Advertisement can only be created from an approved request.")

        # Check if ad already exists to avoid duplicates
        if JobAdvertisement.objects.filter(hiring_request=hiring_request).exists():
            return JobAdvertisement.objects.get(hiring_request=hiring_request)

        # Create draft ad with initial data from request
        ad = JobAdvertisement.objects.create(
            hiring_request=hiring_request,
            title=hiring_request.job_title.title,
            description=hiring_request.purpose,
            requirements="Auto-generated from request. Please update.",
            responsibilities="Auto-generated from request. Please update.",
            status=JobAdvertisement.AdStatus.DRAFT
        )

        # Log Activity (System action)
        ActivityLogService.log_activity(
            user=hiring_request.created_by,  # Attributing to request creator or system user
            company=hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="JobAdvertisement",
            entity_id=ad.id,
            action="AUTO_CREATED_FROM_REQUEST"
        )

        return ad

    @staticmethod
    @transaction.atomic
    def publish_advertisement(ad_id: int, user, data=None):
        """Publishes the job advertisement."""
        ad = JobAdvertisement.objects.select_for_update().get(id=ad_id)
        
        if ad.status != JobAdvertisement.AdStatus.DRAFT:
            raise ValueError("Only draft advertisements can be published.")

        if data:
            for key, value in data.items():
                setattr(ad, key, value)

        ad.status = JobAdvertisement.AdStatus.PUBLISHED
        ad.published_at = timezone.now()
        ad.save()

        # Log Activity
        ActivityLogService.log_activity(
            user=user,
            company=ad.hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="JobAdvertisement",
            entity_id=ad.id,
            action="PUBLISHED",
            new_values=data
        )

        return ad

    @staticmethod
    @transaction.atomic
    def close_advertisement(ad_id: int, user):
        """Closes the job advertisement."""
        ad = JobAdvertisement.objects.select_for_update().get(id=ad_id)
        
        if ad.status != JobAdvertisement.AdStatus.PUBLISHED:
            raise ValueError("Only published advertisements can be closed.")

        ad.status = JobAdvertisement.AdStatus.CLOSED
        ad.closed_at = timezone.now()
        ad.save()

        # Log Activity
        ActivityLogService.log_activity(
            user=user,
            company=ad.hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="JobAdvertisement",
            entity_id=ad.id,
            action="CLOSED"
        )

        return ad
