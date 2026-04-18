import logging
from django.db import transaction
from django.utils import timezone

from apps.hris.travel_management.models import TravelRequest

logger = logging.getLogger(__name__)


class TravelRequestService:

    @staticmethod
    @transaction.atomic
    def create_request(employee_id: int, **data) -> TravelRequest:
        start = data.get("start_date")
        end = data.get("end_date")
        if start and end and start > end:
            raise ValueError("start_date must be before end_date")
        req = TravelRequest.objects.create(employee_id=employee_id, **data)
        logger.info("TravelRequest created: pk=%s employee=%s", req.pk, employee_id)
        return req

    @staticmethod
    @transaction.atomic
    def update_request(request_id: int, employee_id: int, **data) -> TravelRequest:
        req = TravelRequest.objects.filter(
            id=request_id, employee_id=employee_id, is_deleted=False
        ).first()
        if not req:
            raise ValueError("Travel request not found")
        for attr, value in data.items():
            setattr(req, attr, value)
        req.save()
        return req

    @staticmethod
    @transaction.atomic
    def delete_request(request_id: int, employee_id: int) -> None:
        req = TravelRequest.objects.filter(
            id=request_id, employee_id=employee_id, is_deleted=False
        ).first()
        if not req:
            raise ValueError("Travel request not found")
        req.is_deleted = True
        req.deleted_at = timezone.now()
        req.save(update_fields=["is_deleted", "deleted_at"])
        logger.info("TravelRequest cancelled: pk=%s", request_id)
