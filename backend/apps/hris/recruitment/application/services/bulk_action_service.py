"""
BulkActionService — processes bulk operations on recruitment entities.

Returns partial-success responses:
    {"success": [ids], "failed": [{"id": x, "error": "..."}]}

Max 100 IDs per call.

Company isolation: company_id is passed explicitly from the view layer
(resolved via _company_id(request) → tenant id). Never derived from user
attributes, which are not reliable.
"""
import logging

from ...models import HiringRequest, JobAdvertisement, JobApplication
from .hiring_request_service import HiringRequestService
from .job_advertisement_service import JobAdvertisementService
from .application_service import ApplicationService

logger = logging.getLogger(__name__)

MAX_BULK_IDS = 100


class BulkActionService:

    @staticmethod
    def _validate_ids(ids):
        if not ids:
            raise ValueError("ids list cannot be empty.")
        if len(ids) > MAX_BULK_IDS:
            raise ValueError(f"Cannot process more than {MAX_BULK_IDS} IDs at once.")

    @staticmethod
    def _build_result(success, failed):
        return {"success": success, "failed": failed}

    # ── Hiring Requests ────────────────────────────────────────────────────────

    @staticmethod
    def bulk_approve_hiring_requests(ids, user, role_type, note="", company_id=None):
        BulkActionService._validate_ids(ids)
        success, failed = [], []
        for rid in ids:
            try:
                if company_id:
                    hr = HiringRequest.objects.get(pk=rid, company_id=company_id)
                else:
                    hr = HiringRequest.objects.get(pk=rid)
                HiringRequestService.approve_request(hr.pk, user, role_type, note)
                success.append(rid)
            except HiringRequest.DoesNotExist:
                failed.append({"id": rid, "error": "Not found in your company."})
            except Exception as e:
                failed.append({"id": rid, "error": str(e)})
        return BulkActionService._build_result(success, failed)

    @staticmethod
    def bulk_reject_hiring_requests(ids, user, role_type, reason, company_id=None):
        BulkActionService._validate_ids(ids)
        success, failed = [], []
        for rid in ids:
            try:
                if company_id:
                    hr = HiringRequest.objects.get(pk=rid, company_id=company_id)
                else:
                    hr = HiringRequest.objects.get(pk=rid)
                HiringRequestService.reject_request(hr.pk, user, role_type, reason)
                success.append(rid)
            except HiringRequest.DoesNotExist:
                failed.append({"id": rid, "error": "Not found in your company."})
            except Exception as e:
                failed.append({"id": rid, "error": str(e)})
        return BulkActionService._build_result(success, failed)

    @staticmethod
    def bulk_delete_hiring_requests(ids, user, company_id=None):
        BulkActionService._validate_ids(ids)
        success, failed = [], []
        for rid in ids:
            try:
                if company_id:
                    hr = HiringRequest.objects.get(pk=rid, company_id=company_id)
                else:
                    hr = HiringRequest.objects.get(pk=rid)
                HiringRequestService.soft_delete_hiring_request(hr.pk, user)
                success.append(rid)
            except HiringRequest.DoesNotExist:
                failed.append({"id": rid, "error": "Not found in your company."})
            except Exception as e:
                failed.append({"id": rid, "error": str(e)})
        return BulkActionService._build_result(success, failed)

    # ── Job Advertisements ─────────────────────────────────────────────────────

    @staticmethod
    def bulk_publish_advertisements(ids, user, company_id=None):
        BulkActionService._validate_ids(ids)
        success, failed = [], []
        for aid in ids:
            try:
                qs = JobAdvertisement.objects.select_related("hiring_request")
                if company_id:
                    ad = qs.get(pk=aid, hiring_request__company_id=company_id)
                else:
                    ad = qs.get(pk=aid)
                JobAdvertisementService.publish_advertisement(ad.pk, user)
                success.append(aid)
            except JobAdvertisement.DoesNotExist:
                failed.append({"id": aid, "error": "Not found in your company."})
            except Exception as e:
                failed.append({"id": aid, "error": str(e)})
        return BulkActionService._build_result(success, failed)

    @staticmethod
    def bulk_close_advertisements(ids, user, company_id=None):
        BulkActionService._validate_ids(ids)
        success, failed = [], []
        for aid in ids:
            try:
                qs = JobAdvertisement.objects.select_related("hiring_request")
                if company_id:
                    ad = qs.get(pk=aid, hiring_request__company_id=company_id)
                else:
                    ad = qs.get(pk=aid)
                JobAdvertisementService.close_advertisement(ad.pk, user)
                success.append(aid)
            except JobAdvertisement.DoesNotExist:
                failed.append({"id": aid, "error": "Not found in your company."})
            except Exception as e:
                failed.append({"id": aid, "error": str(e)})
        return BulkActionService._build_result(success, failed)

    # ── Job Applications ───────────────────────────────────────────────────────

    @staticmethod
    def bulk_edit_applications(ids, user, classification, company_id=None):
        BulkActionService._validate_ids(ids)
        valid_choices = [c[0] for c in JobApplication.Classification.choices]
        if classification not in valid_choices:
            raise ValueError(
                f"Invalid classification '{classification}'. Must be one of: {valid_choices}"
            )
        success, failed = [], []
        for app_id in ids:
            try:
                qs = JobApplication.objects.select_related("candidate")
                if company_id:
                    app = qs.get(pk=app_id, candidate__company_id=company_id)
                else:
                    app = qs.get(pk=app_id)
                ApplicationService.move_to_stage(app.pk, app.status, user, classification)
                success.append(app_id)
            except JobApplication.DoesNotExist:
                failed.append({"id": app_id, "error": "Not found in your company."})
            except Exception as e:
                failed.append({"id": app_id, "error": str(e)})
        return BulkActionService._build_result(success, failed)
