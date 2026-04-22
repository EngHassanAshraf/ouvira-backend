import logging
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.hris.leave_management.models import LeaveRequest, LeaveType, LeaveActivityLog

logger = logging.getLogger(__name__)


class LeaveRequestService:

    @staticmethod
    @transaction.atomic
    def create_leave_request(
        employee_id: int,
        leave_type_id: int,
        start_date,
        end_date,
        details: str = None,
        attachment=None,
        created_by_id: int = None,  # Manager behalf uchun
    ) -> LeaveRequest:
        """
        Yangi ta'til so'rovi yaratish.
        - Overlap tekshiruv
        - Balance tekshiruv
        - Duration avtomatik hisoblanadi
        """

        # 1. Leave type mavjudligini tekshiramiz
        leave_type = LeaveType.objects.filter(
            id=leave_type_id, is_active=True, is_deleted=False
        ).first()
        if not leave_type:
            raise ValidationError("Invalid or inactive leave type.")

        # 2. Sana tekshiruvi
        if end_date < start_date:
            raise ValidationError("End date must be the same as or later than the start date.")

        # 3. Start date o'tmishda bo'lmasligi kerak
        if start_date < timezone.now().date():
            raise ValidationError("Start date cannot be earlier than today.")

        # 4. Overlap tekshiruvi — Pending yoki Approved so'rov bormi?
        LeaveRequestService._check_overlap(employee_id, start_date, end_date)

        # 5. Balance tekshiruvi
        LeaveRequestService._check_balance(employee_id, leave_type_id, start_date, end_date)

        # 6. So'rov yaratamiz
        leave_request = LeaveRequest.objects.create(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            start_date=start_date,
            end_date=end_date,
            details=details,
            attachment=attachment,
            created_by_id=created_by_id,
            status=LeaveRequest.StatusChoice.PENDING,
        )

        # 7. Activity log
        LeaveActivityLog.objects.create(
            leave_request=leave_request,
            performed_by_id=created_by_id or employee_id,
            action=LeaveActivityLog.ActionChoice.SUBMITTED,
        )

        logger.info(f"Leave request created: employee_id={employee_id}, id={leave_request.id}")
        return leave_request

    @staticmethod
    @transaction.atomic
    def update_leave_request(
        leave_request_id: int,
        employee_id: int,
        **data
    ) -> LeaveRequest:
        """
        Ta'til so'rovini tahrirlash.
        Faqat PENDING holatida tahrirlasa bo'ladi.
        """
        leave_request = LeaveRequest.objects.filter(
            id=leave_request_id,
            employee_id=employee_id,
            is_deleted=False
        ).first()

        if not leave_request:
            raise ValueError("Leave request not found.")

        if leave_request.status != LeaveRequest.StatusChoice.PENDING:
            raise ValidationError("You can only edit requests that are in 'Pending' status.")

        # Agar sana o'zgarsa — overlap tekshiramiz
        start_date = data.get("start_date", leave_request.start_date)
        end_date = data.get("end_date", leave_request.end_date)

        if start_date != leave_request.start_date or end_date != leave_request.end_date:
            if end_date < start_date:
                raise ValidationError("End date must be the same as or later than the start date.")
            LeaveRequestService._check_overlap(
                employee_id, start_date, end_date, exclude_id=leave_request_id
            )

        for attr, value in data.items():
            setattr(leave_request, attr, value)

        leave_request.save()

        # Activity log
        LeaveActivityLog.objects.create(
            leave_request=leave_request,
            performed_by_id=employee_id,
            action=LeaveActivityLog.ActionChoice.UPDATED,
        )

        logger.info(f"Leave request updated: id={leave_request_id}")
        return leave_request

    @staticmethod
    @transaction.atomic
    def cancel_leave_request(
        leave_request_id: int,
        employee_id: int,
    ) -> LeaveRequest:
        """
        Ta'til so'rovini bekor qilish.
        Faqat start_date dan oldin bekor qilsa bo'ladi.
        """
        leave_request = LeaveRequest.objects.filter(
            id=leave_request_id,
            employee_id=employee_id,
            is_deleted=False
        ).first()

        if not leave_request:
            raise ValueError("Leave request not found.")

        if leave_request.status in [
            LeaveRequest.StatusChoice.DECLINED,
            LeaveRequest.StatusChoice.CANCELLED,
        ]:
            raise ValidationError("This request cannot be cancelled.")

        if leave_request.status == LeaveRequest.StatusChoice.APPROVED:
            from apps.hris.leave_management.services.leave_balance_services import LeaveBalanceService
            LeaveBalanceService.refund_balance(
                employee_id=leave_request.employee_id,
                leave_type_id=leave_request.leave_type_id,
                year=leave_request.start_date.year,
                days=leave_request.duration,
            )

        leave_request.status = LeaveRequest.StatusChoice.CANCELLED
        leave_request.cancelled_at = timezone.now()
        leave_request.save()

        # Activity log
        LeaveActivityLog.objects.create(
            leave_request=leave_request,
            performed_by_id=employee_id,
            action=LeaveActivityLog.ActionChoice.CANCELLED,
        )

        logger.info(f"Leave request cancelled: id={leave_request_id}")
        return leave_request

    # -------------------------------------------------------
    # Private helper metodlar
    # -------------------------------------------------------

    @staticmethod
    def _check_overlap(employee_id: int, start_date, end_date, exclude_id: int = None):
        """
        Xodimning shu sanada Pending yoki Approved so'rovi bormi?
        """
        qs = LeaveRequest.objects.filter(
            employee_id=employee_id,
            is_deleted=False,
            status__in=[
                LeaveRequest.StatusChoice.PENDING,
                LeaveRequest.StatusChoice.MANAGER_APPROVED,
                LeaveRequest.StatusChoice.APPROVED,
            ],
            start_date__lte=end_date,
            end_date__gte=start_date,
        )
        if exclude_id:
            qs = qs.exclude(id=exclude_id)

        if qs.exists():
            raise ValidationError(
                "You already have a leave request submitted for this period."
            )

    @staticmethod
    def _check_balance(employee_id: int, leave_type_id: int, start_date, end_date):
        """
        Xodimning yetarli balansi bormi?
        """
        from apps.hris.leave_management.models import LeaveBalance

        duration = (end_date - start_date).days + 1
        year = start_date.year

        balance = LeaveBalance.objects.filter(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            year=year,
        ).first()

        if not balance:
            raise ValidationError("No leave balance found for this leave type.")

        if balance.remaining_days < duration:
            raise ValidationError(
                f"Insufficient leave balance. "
                f"Remaining: {balance.remaining_days} days, Requested: {duration} days."
            )