import logging
from django.db import transaction
from django.utils import timezone
from apps.audit.services.activity_log_service import ActivityLogService
from apps.audit.utils import get_or_create_date_dim
from ...models import HiringRequest, JobAdvertisement
from .recruitment_audit_service import RecruitmentAuditService

logger = logging.getLogger(__name__)

# Fields that are safe to update on a JobAdvertisement
_EDITABLE_FIELDS = {
    "title", "description", "requirements", "skills",
    "responsibilities", "city", "area", "deadline", "platforms",
}

# Fields that can be updated while the ad is published (non-structural changes only)
_PUBLISHED_EDITABLE_FIELDS = {"deadline", "platforms"}


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

        if JobAdvertisement.objects.filter(hiring_request=hiring_request).exists():
            return JobAdvertisement.objects.get(hiring_request=hiring_request)

        ad = JobAdvertisement.objects.create(
            hiring_request=hiring_request,
            title=hiring_request.job_title.title,
            description=hiring_request.purpose,
            requirements="Auto-generated from request. Please update.",
            responsibilities="Auto-generated from request. Please update.",
            status=JobAdvertisement.AdStatus.DRAFT
        )

        ActivityLogService.log_activity(
            user=hiring_request.created_by,
            company=hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="JobAdvertisement",
            entity_id=ad.id,
            action="AUTO_CREATED_FROM_REQUEST"
        )

        return ad

    @staticmethod
    @transaction.atomic
    def update_advertisement(ad_id: int, user, data: dict) -> JobAdvertisement:
        """
        Updates a Job Advertisement.

        Rules:
        - DRAFT ads: all content fields can be edited.
        - PUBLISHED ads: only deadline and platforms can be updated
          (structural content is locked once live).
        - CLOSED ads: cannot be edited at all.
        """
        ad = JobAdvertisement.objects.select_for_update().select_related(
            "hiring_request__company"
        ).get(id=ad_id)

        if ad.status == JobAdvertisement.AdStatus.CLOSED:
            raise ValueError("Closed advertisements cannot be edited.")

        allowed = (
            _EDITABLE_FIELDS
            if ad.status == JobAdvertisement.AdStatus.DRAFT
            else _PUBLISHED_EDITABLE_FIELDS
        )

        rejected = set(data.keys()) - allowed - {"hiring_request"}
        if rejected:
            raise ValueError(
                f"The following fields cannot be updated on a "
                f"'{ad.status}' advertisement: {', '.join(sorted(rejected))}."
            )

        old_values = {f: getattr(ad, f) for f in allowed if f in data}

        changed = False
        for field, value in data.items():
            if field not in allowed:
                continue
            if getattr(ad, field) != value:
                setattr(ad, field, value)
                changed = True

        if changed:
            ad.save()
            ActivityLogService.log_activity(
                user=user,
                company=ad.hiring_request.company,
                date_dim=get_or_create_date_dim(timezone.now().date()),
                entity_type="JobAdvertisement",
                entity_id=ad.id,
                action="UPDATED",
                old_values={k: str(v) for k, v in old_values.items()},
                new_values={k: str(data[k]) for k in old_values}
            )

        return ad

    @staticmethod
    @transaction.atomic
    def publish_advertisement(ad_id: int, user, data=None):
        """
        Publishes the job advertisement.
        Accepts optional deadline and platforms overrides at publish time.
        """
        ad = JobAdvertisement.objects.select_for_update().select_related(
            "hiring_request__company"
        ).get(id=ad_id)

        if ad.status != JobAdvertisement.AdStatus.DRAFT:
            raise ValueError("Only draft advertisements can be published.")

        # Apply safe publish-time overrides (deadline, platforms only)
        if data:
            for field in _PUBLISHED_EDITABLE_FIELDS:
                if field in data:
                    setattr(ad, field, data[field])

        ad.status = JobAdvertisement.AdStatus.PUBLISHED
        ad.published_at = timezone.now()
        ad.save()

        ActivityLogService.log_activity(
            user=user,
            company=ad.hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="JobAdvertisement",
            entity_id=ad.id,
            action="PUBLISHED",
            new_values={
                "deadline": str(ad.deadline),
                "platforms": ad.platforms,
            }
        )

        RecruitmentAuditService.log(
            user=user,
            company=ad.hiring_request.company,
            entity_type="job_advertisement",
            entity_id=ad.pk,
            action="published",
            entity_label=ad.title,
        )

        return ad

    @staticmethod
    @transaction.atomic
    def close_advertisement(ad_id: int, user):
        """Closes the job advertisement."""
        ad = JobAdvertisement.objects.select_for_update().select_related(
            "hiring_request__company"
        ).get(id=ad_id)

        if ad.status != JobAdvertisement.AdStatus.PUBLISHED:
            raise ValueError("Only published advertisements can be closed.")

        ad.status = JobAdvertisement.AdStatus.CLOSED
        ad.closed_at = timezone.now()
        ad.save()

        ActivityLogService.log_activity(
            user=user,
            company=ad.hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="JobAdvertisement",
            entity_id=ad.id,
            action="CLOSED"
        )

        RecruitmentAuditService.log(
            user=user,
            company=ad.hiring_request.company,
            entity_type="job_advertisement",
            entity_id=ad.pk,
            action="closed",
            entity_label=ad.title,
        )

        return ad

    @staticmethod
    @transaction.atomic
    def reopen_advertisement(ad_id: int, user) -> JobAdvertisement:
        """
        Reopens a closed advertisement back to DRAFT for revision.

        Rules:
        - Only CLOSED ads can be reopened.
        - Clears closed_at so it can be re-published cleanly.
        """
        ad = JobAdvertisement.objects.select_for_update().select_related(
            "hiring_request__company"
        ).get(id=ad_id)

        if ad.status != JobAdvertisement.AdStatus.CLOSED:
            raise ValueError("Only closed advertisements can be reopened.")

        ad.status = JobAdvertisement.AdStatus.DRAFT
        ad.closed_at = None
        ad.save()

        ActivityLogService.log_activity(
            user=user,
            company=ad.hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="JobAdvertisement",
            entity_id=ad.id,
            action="REOPENED"
        )

        RecruitmentAuditService.log(
            user=user,
            company=ad.hiring_request.company,
            entity_type="job_advertisement",
            entity_id=ad.pk,
            action="reopened",
            entity_label=ad.title,
        )

        return ad

    @staticmethod
    @transaction.atomic
    def soft_delete_advertisement(ad_id: int, user) -> None:
        """
        Soft-deletes a Job Advertisement.

        Rules:
        - Only DRAFT ads can be deleted.
        - Published/closed ads must be closed first.
        """
        ad = JobAdvertisement.objects.select_for_update().select_related(
            "hiring_request__company"
        ).get(id=ad_id)

        if ad.status != JobAdvertisement.AdStatus.DRAFT:
            raise ValueError(
                f"Cannot delete a '{ad.status}' advertisement. "
                "Close it first, or only draft advertisements can be deleted."
            )

        ad.is_deleted = True
        ad.deleted_at = timezone.now()
        ad.save(update_fields=["is_deleted", "deleted_at"])

        ActivityLogService.log_activity(
            user=user,
            company=ad.hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="JobAdvertisement",
            entity_id=ad.id,
            action="DELETED"
        )
