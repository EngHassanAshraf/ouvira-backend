import logging
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.hris.travel_management.models import (
    BusinessTripRequest,
    BusinessTripActivityLog,
)

logger = logging.getLogger(__name__)


class BusinessTripApprovalService:

    @staticmethod
    @transaction.atomic
    def manager_approve(
        trip_request_id: int,
        manager_id: int,
        company_id: int,
    ) -> BusinessTripRequest:
        """
        1-bosqich: Manager tasdiqlaydi.
        PENDING → MANAGER_APPROVED

        Step 1: Manager approves.
        PENDING → MANAGER_APPROVED
        """
        trip_request = BusinessTripApprovalService._get_request(trip_request_id, company_id)

        if trip_request.status != BusinessTripRequest.StatusChoice.PENDING:
            raise ValidationError("Only 'Pending' requests can be approved by manager.")

        trip_request.status               = BusinessTripRequest.StatusChoice.MANAGER_APPROVED
        trip_request.manager_approved_by_id = manager_id
        trip_request.manager_approved_at  = timezone.now()
        trip_request.save()

        BusinessTripActivityLog.objects.create(
            trip_request=trip_request,
            performed_by_id=manager_id,
            action=BusinessTripActivityLog.ActionChoice.MANAGER_APPROVED,
            note="Manager approved",
            company_id=company_id,
        )

        logger.info(f"Manager approved trip: id={trip_request_id}, manager_id={manager_id}")
        return trip_request


    @staticmethod
    @transaction.atomic
    def hr_approve(
        trip_request_id: int,
        hr_id: int,
        company_id: int,
    ) -> BusinessTripRequest:
        """
        2-bosqich: HR Director tasdiqlaydi.
        MANAGER_APPROVED → APPROVED
        Tasdiqlanganda balance.used_days avtomatik yangilanadi.

        Step 2: HR Director approves.
        MANAGER_APPROVED → APPROVED
        Balance.used_days is automatically updated.
        """
        trip_request = BusinessTripApprovalService._get_request(trip_request_id, company_id)

        if trip_request.status != BusinessTripRequest.StatusChoice.MANAGER_APPROVED:
            raise ValidationError("Request must be approved by manager first.")

        trip_request.status            = BusinessTripRequest.StatusChoice.APPROVED
        trip_request.hr_approved_by_id = hr_id
        trip_request.hr_approved_at    = timezone.now()
        trip_request.save()

        from apps.hris.travel_management.services.balance_service import BusinessTripBalanceService
        BusinessTripBalanceService.deduct_balance(
            employee_id=trip_request.employee_id,
            company_id=company_id,
            year=trip_request.start_date.year,
            days=trip_request.duration,
        )

        BusinessTripActivityLog.objects.create(
            trip_request=trip_request,
            performed_by_id=hr_id,
            action=BusinessTripActivityLog.ActionChoice.HR_APPROVED,
            note="HR Director approved",
            company_id=company_id,
        )

        logger.info(f"HR approved trip: id={trip_request_id}, hr_id={hr_id}")
        return trip_request


    @staticmethod
    @transaction.atomic
    def decline(
        trip_request_id: int,
        declined_by_id: int,
        company_id: int,
        reason: str,
    ) -> BusinessTripRequest:
        """
        Rad etish — istalgan bosqichda (Manager yoki HR).
        Reason majburiy!

        Decline at any step. Reason is mandatory!
        """
        if not reason or not reason.strip():
            raise ValidationError("Decline reason is required.")

        trip_request = BusinessTripApprovalService._get_request(trip_request_id, company_id)

        if trip_request.status not in [
            BusinessTripRequest.StatusChoice.PENDING,
            BusinessTripRequest.StatusChoice.MANAGER_APPROVED,
        ]:
            raise ValidationError("Only Pending or Manager Approved requests can be declined.")

        trip_request.status          = BusinessTripRequest.StatusChoice.DECLINED
        trip_request.decline_reason  = reason
        trip_request.declined_by_id  = declined_by_id
        trip_request.declined_at     = timezone.now()
        trip_request.save()

        BusinessTripActivityLog.objects.create(
            trip_request=trip_request,
            performed_by_id=declined_by_id,
            action=BusinessTripActivityLog.ActionChoice.DECLINED,
            note=reason,
            company_id=company_id,
        )

        logger.info(f"Trip request declined: id={trip_request_id}")
        return trip_request


    @staticmethod
    @transaction.atomic
    def interrupt(
        trip_request_id: int,
        interrupted_by_id: int,
        company_id: int,
        interruption_date,
    ) -> BusinessTripRequest:
        """
        Aktiv xizmat safarini to'xtatish (manual trigger).
        Faqat ACTIVE statusda ishlaydi.

        Interrupt an active trip (manual trigger).
        Only works when status is ACTIVE.
        """
        trip_request = BusinessTripApprovalService._get_request(trip_request_id, company_id)

        if trip_request.status != BusinessTripRequest.StatusChoice.ACTIVE:
            raise ValidationError("Only active trips can be interrupted.")

        if not (trip_request.start_date <= interruption_date <= trip_request.end_date):
            raise ValidationError("Interruption date must fall within the trip period.")

        trip_request.status            = BusinessTripRequest.StatusChoice.INTERRUPTED
        trip_request.interrupted_by_id = interrupted_by_id
        trip_request.interruption_date = interruption_date
        trip_request.interrupted_at    = timezone.now()
        trip_request.save()

        BusinessTripActivityLog.objects.create(
            trip_request=trip_request,
            performed_by_id=interrupted_by_id,
            action=BusinessTripActivityLog.ActionChoice.INTERRUPTED,
            note=f"Interrupted on {interruption_date}",
            company_id=company_id,
        )

        logger.info(f"Trip interrupted: id={trip_request_id}, date={interruption_date}")
        return trip_request


    @staticmethod
    @transaction.atomic
    def bulk_approve(
        trip_request_ids: list,
        approved_by_id: int,
        company_id: int,
        step: str = "manager",
    ) -> dict:
        """Bir vaqtda ko'p so'rovlarni tasdiqlash. / Bulk approve."""
        results = {"approved": [], "failed": []}

        for request_id in trip_request_ids:
            try:
                if step == "manager":
                    BusinessTripApprovalService.manager_approve(request_id, approved_by_id, company_id)
                else:
                    BusinessTripApprovalService.hr_approve(request_id, approved_by_id, company_id)
                results["approved"].append(request_id)
            except Exception as e:
                results["failed"].append({"id": request_id, "error": str(e)})

        return results


    @staticmethod
    @transaction.atomic
    def bulk_decline(
        trip_request_ids: list,
        declined_by_id: int,
        company_id: int,
        reason: str,
    ) -> dict:
        """Bir vaqtda ko'p so'rovlarni rad etish. / Bulk decline."""
        results = {"declined": [], "failed": []}

        for request_id in trip_request_ids:
            try:
                BusinessTripApprovalService.decline(request_id, declined_by_id, company_id, reason)
                results["declined"].append(request_id)
            except Exception as e:
                results["failed"].append({"id": request_id, "error": str(e)})

        return results



    # Private helper

    @staticmethod
    def _get_request(trip_request_id: int, company_id: int) -> BusinessTripRequest:
        trip_request = BusinessTripRequest.objects.filter(
            id=trip_request_id,
            company_id=company_id,
            is_deleted=False,
        ).first()
        if not trip_request:
            raise ValueError("Business trip request not found.")
        return trip_request