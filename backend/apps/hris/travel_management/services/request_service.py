import logging
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.hris.travel_management.models import (
    BusinessTripRequest,
    BusinessTripActivityLog,
)

logger = logging.getLogger(__name__)


class BusinessTripRequestService:

    @staticmethod
    @transaction.atomic
    def create_request(
        employee_id: int,
        company_id: int,
        destination: str,
        start_date,
        end_date,
        details: str = None,
        benefit_ids: list = None,
        attachments: list = None,
        created_by_id: int = None,  # Manager on behalf of uchun
    ) -> BusinessTripRequest:
        """
        Yangi xizmat safari so'rovi yaratish.
        - Sana tekshiruvi
        - Overlap tekshiruvi
        - Duration avtomatik hisoblanadi (save da)
        - Activity log yoziladi

        Create a new business trip request.
        - Date validation
        - Overlap check
        - Duration auto-calculated (in save)
        - Activity log recorded
        """

        # 1. Sana tekshiruvi
        if end_date < start_date:
            raise ValidationError("End date must be the same as or later than the start date.")

        if start_date < timezone.now().date():
            raise ValidationError("Start date cannot be earlier than today.")

        # 2. Overlap tekshiruvi
        BusinessTripRequestService._check_overlap(employee_id, start_date, end_date)

        # 3. So'rov yaratamiz
        trip_request = BusinessTripRequest.objects.create(
            employee_id=employee_id,
            company_id=company_id,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            details=details,
            attachments=attachments or [],
            created_by_id=created_by_id,
            status=BusinessTripRequest.StatusChoice.PENDING,
        )

        # 4. Benefits qo'shamiz (M2M)
        if benefit_ids:
            trip_request.benefits.set(benefit_ids)

        # 5. Activity log
        BusinessTripActivityLog.objects.create(
            trip_request=trip_request,
            performed_by_id=created_by_id or employee_id,
            action=BusinessTripActivityLog.ActionChoice.SUBMITTED,
            company_id=company_id,
        )

        logger.info(f"Business trip request created: employee_id={employee_id}, id={trip_request.id}")
        return trip_request

    @staticmethod
    @transaction.atomic
    def update_request(
        trip_request_id: int,
        employee_id: int,
        company_id: int,
        **data,
    ) -> BusinessTripRequest:
        """
        Xizmat safari so'rovini tahrirlash.
        Faqat PENDING holatida tahrirlasa bo'ladi.

        Update a business trip request.
        Only allowed when status is PENDING.
        """
        trip_request = BusinessTripRequest.objects.filter(
            id=trip_request_id,
            employee_id=employee_id,
            company_id=company_id,
            is_deleted=False,
        ).first()

        if not trip_request:
            raise ValueError("Business trip request not found.")

        if trip_request.status != BusinessTripRequest.StatusChoice.PENDING:
            raise ValidationError("You can only edit requests that are in 'Pending' status.")

        # Sana o'zgarsa — overlap tekshiramiz
        start_date = data.get("start_date", trip_request.start_date)
        end_date   = data.get("end_date", trip_request.end_date)

        if start_date != trip_request.start_date or end_date != trip_request.end_date:
            if end_date < start_date:
                raise ValidationError("End date must be the same as or later than the start date.")
            BusinessTripRequestService._check_overlap(
                employee_id, start_date, end_date, exclude_id=trip_request_id
            )

        # Benefits alohida (M2M)
        benefit_ids = data.pop("benefit_ids", None)

        for attr, value in data.items():
            setattr(trip_request, attr, value)

        trip_request.save()

        if benefit_ids is not None:
            trip_request.benefits.set(benefit_ids)

        # Activity log
        BusinessTripActivityLog.objects.create(
            trip_request=trip_request,
            performed_by_id=employee_id,
            action=BusinessTripActivityLog.ActionChoice.UPDATED,
            company_id=company_id,
        )

        logger.info(f"Business trip request updated: id={trip_request_id}")
        return trip_request

    @staticmethod
    @transaction.atomic
    def cancel_request(
        trip_request_id: int,
        employee_id: int,
        company_id: int,
    ) -> BusinessTripRequest:
        """
        Xizmat safari so'rovini bekor qilish.
        PENDING yoki MANAGER_APPROVED holatida bekor qilsa bo'ladi.

        Cancel a business trip request.
        Allowed when status is PENDING or MANAGER_APPROVED.
        """
        trip_request = BusinessTripRequest.objects.filter(
            id=trip_request_id,
            employee_id=employee_id,
            company_id=company_id,
            is_deleted=False,
        ).first()

        if not trip_request:
            raise ValueError("Business trip request not found.")

        if trip_request.status not in [
            BusinessTripRequest.StatusChoice.PENDING,
            BusinessTripRequest.StatusChoice.MANAGER_APPROVED,
        ]:
            raise ValidationError("Only Pending or Manager Approved requests can be cancelled.")

        trip_request.status     = BusinessTripRequest.StatusChoice.CANCELLED
        trip_request.cancelled_at = timezone.now()
        trip_request.save()

        # Activity log
        BusinessTripActivityLog.objects.create(
            trip_request=trip_request,
            performed_by_id=employee_id,
            action=BusinessTripActivityLog.ActionChoice.CANCELLED,
            company_id=company_id,
        )

        logger.info(f"Business trip request cancelled: id={trip_request_id}")
        return trip_request

    # -------------------------------------------------------
    # Private helper metodlar
    # -------------------------------------------------------

    @staticmethod
    def _check_overlap(employee_id: int, start_date, end_date, exclude_id: int = None):
        """
        Xodimning shu sanada Pending, Manager Approved yoki Approved so'rovi bormi?

        Check if employee has an overlapping trip request.
        """
        qs = BusinessTripRequest.objects.filter(
            employee_id=employee_id,
            is_deleted=False,
            status__in=[
                BusinessTripRequest.StatusChoice.PENDING,
                BusinessTripRequest.StatusChoice.MANAGER_APPROVED,
                BusinessTripRequest.StatusChoice.APPROVED,
                BusinessTripRequest.StatusChoice.ACTIVE,
            ],
            start_date__lte=end_date,
            end_date__gte=start_date,
        )
        if exclude_id:
            qs = qs.exclude(id=exclude_id)

        if qs.exists():
            raise ValidationError(
                "You already have a business trip request submitted for this period."
            )
