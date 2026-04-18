"""
JobBoardSyncService — placeholder for future job board integrations.
Currently returns synced=0 for all platforms.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from ...models import JobAdvertisement

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    synced: int = 0
    skipped_duplicates: int = 0
    platforms_attempted: List[str] = field(default_factory=list)
    synced_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


class JobBoardSyncService:

    SUPPORTED_PLATFORMS = {"linkedin", "bayt", "facebook", "internal"}

    @staticmethod
    def sync(job_advertisement_id, platforms, company_id) -> SyncResult:
        """
        Placeholder sync. Validates inputs, returns empty result.
        Real integration to be implemented per platform.
        """
        if not platforms:
            raise ValueError("platforms list cannot be empty.")

        try:
            ad = JobAdvertisement.objects.select_related("hiring_request__company").get(
                pk=job_advertisement_id,
                hiring_request__company_id=company_id,
            )
        except JobAdvertisement.DoesNotExist:
            raise ValueError(f"Job advertisement {job_advertisement_id} not found or not published.")

        if ad.status != JobAdvertisement.AdStatus.PUBLISHED:
            raise ValueError("Can only sync from published job advertisements.")

        logger.info(
            "JobBoardSyncService.sync called for ad=%s platforms=%s (placeholder — no real sync)",
            job_advertisement_id, platforms
        )

        return SyncResult(
            synced=0,
            skipped_duplicates=0,
            platforms_attempted=list(platforms),
        )
