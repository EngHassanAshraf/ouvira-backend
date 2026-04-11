"""
BulkActionService — processes bulk operations on recruitment entities.
Returns partial-success responses: {"success": [ids], "failed": [{"id": x, "error": "..."}]}
Max 100 IDs per call.
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

    @staticmethod
    def bulk_approve_hiring_requests(ids, user, role_type, note=""):
        BulkActionService._validate_ids(ids)
        success, failed = [], []
        company_id = getattr(getattr(user, 'company', None), 'id', None) or getattr(user, 'company_id', None)
        for rid in ids:
            try:
                hr = HiringRequest.objects.get(pk=rid)
                if company_id and str(hr.company_id) != str(company_id):
                    failed.append({"id": rid, "error": "Not found in your company."})
                    continue
                HiringRequestService.approve_request(rid, user, role_type, note)
                success.append(rid)
            except Exception as e:
                failed.append({"id": rid, "error": str(e)})
        return BulkActionService._build_result(success, failed)

    @staticmethod
    def bulk_reject_hiring_requests(ids, user, role_type, reason):
        BulkActionService._validate_ids(ids)
        success, failed = [], []
        company_id = getattr(getattr(user, 'company', None), 'id', None) or getattr(user, 'company_id', None)
        for rid in ids:
            try:
                hr = HiringRequest.objects.get(pk=rid)
                if company_id and str(hr.company_id) != str(company_id):
                    failed.append({"id": rid, "error": "Not found in your company."})
                    continue
                HiringRequestService.reject_request(rid, user, role_type, reason)
                success.append(rid)
            except Exception as e:
                failed.append({"id": rid, "error": str(e)})
        return BulkActionService._build_result(success, failed)

    @staticmethod
    def bulk_delete_hiring_requests(ids, user):
        BulkActionService._validate_ids(ids)
        success, failed = [], []
        company_id = getattr(getattr(user, 'company', None), 'id', None) or getattr(user, 'company_id', None)
        for rid in ids:
            try:
                hr = HiringRequest.objects.get(pk=rid)
                if company_id and str(hr.company_id) != str(company_id):
                    failed.append({"id": rid, "error": "Not found in your company."})
                    continue
                HiringRequestService.soft_delete_hiring_request(rid, user)
                success.append(rid)
            except Exception as e:
                failed.append({"id": rid, "error": str(e)})
        return BulkActionService._build_result(success, failed)

    @staticmethod
    def bulk_publish_advertisements(ids, user):
        BulkActionService._validate_ids(ids)
        success, failed = [], []
        company_id = getattr(getattr(user, 'company', None), 'id', None) or getattr(user, 'company_id', None)
        for aid in ids:
            try:
                ad = JobAdvertisement.objects.select_related("hiring_request__company").get(pk=aid)
                if company_id and str(ad.hiring_request.company_id) != str(company_id):
                    failed.append({"id": aid, "error": "Not found in your company."})
                    continue
                JobAdvertisementService.publish_advertisement(aid, user)
                success.append(aid)
            except Exception as e:
                failed.append({"id": aid, "error": str(e)})
        return BulkActionService._build_result(success, failed)

    @staticmethod
    def bulk_close_advertisements(ids, user):
        BulkActionService._validate_ids(ids)
        success, failed = [], []
        company_id = getattr(getattr(user, 'company', None), 'id', None) or getattr(user, 'company_id', None)
        for aid in ids:
            try:
                ad = JobAdvertisement.objects.select_related("hiring_request__company").get(pk=aid)
                if company_id and str(ad.hiring_request.company_id) != str(company_id):
                    failed.append({"id": aid, "error": "Not found in your company."})
                    continue
                JobAdvertisementService.close_advertisement(aid, user)
                success.append(aid)
            except Exception as e:
                failed.append({"id": aid, "error": str(e)})
        return BulkActionService._build_result(success, failed)

    @staticmethod
    def bulk_edit_applications(ids, user, classification):
        BulkActionService._validate_ids(ids)
        valid_choices = [c[0] for c in JobApplication.Classification.choices]
        if classification not in valid_choices:
            raise ValueError(f"Invalid classification '{classification}'. Must be one of: {valid_choices}")
        success, failed = [], []
        company_id = getattr(getattr(user, 'company', None), 'id', None) or getattr(user, 'company_id', None)
        for app_id in ids:
            try:
                app = JobApplication.objects.select_related(
                    "candidate", "job_advertisement__hiring_request__company"
                ).get(pk=app_id)
                if company_id and str(app.candidate.company_id) != str(company_id):
                    failed.append({"id": app_id, "error": "Not found in your company."})
                    continue
                ApplicationService.move_to_stage(app_id, app.status, user, classification)
                success.append(app_id)
            except Exception as e:
                failed.append({"id": app_id, "error": str(e)})
        return BulkActionService._build_result(success, failed)
