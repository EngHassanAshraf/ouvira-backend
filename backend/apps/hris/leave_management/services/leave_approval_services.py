import logging
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.hris.leave_management.models import LeaveRequest, LeaveActivityLog

logger = logging.getLogger(__name__)


class LeaveApprovalService:

    @staticmethod
    @transaction.atomic
    def manager_approve(
        leave_request_id: int,
        manager_id: int,
    ) -> LeaveRequest:
        """
        1-bosqich: Direct Manager tasdiqlaydi.
        PENDING → MANAGER_APPROVED
        """
        leave_request = LeaveApprovalService._get_pending_request(leave_request_id)

        if leave_request.status != LeaveRequest.StatusChoice.PENDING:
            raise ValidationError("Only 'Pending' requests can be approved by manager.")

        leave_request.status = LeaveRequest.StatusChoice.MANAGER_APPROVED
        leave_request.manager_approved_by_id = manager_id
        leave_request.manager_approved_at = timezone.now()
        leave_request.save()

        LeaveActivityLog.objects.create(
            leave_request=leave_request,
            performed_by_id=manager_id,
            action=LeaveActivityLog.ActionChoice.APPROVED,
            note="Manager approved",
        )

        logger.info(f"Manager approved leave request: id={leave_request_id}, manager_id={manager_id}")
        return leave_request

    @staticmethod
    @transaction.atomic
    def hr_approve(
        leave_request_id: int,
        hr_id: int,
    ) -> LeaveRequest:
        """
        2-bosqich: HR Director tasdiqlaydi.
        MANAGER_APPROVED → APPROVED
        Tasdiqlanganda balance avtomatik ayiriladi.
        """
        leave_request = LeaveRequest.objects.filter(
            id=leave_request_id, is_deleted=False
        ).first()

        if not leave_request:
            raise ValueError("Leave request not found.")

        if leave_request.status != LeaveRequest.StatusChoice.MANAGER_APPROVED:
            raise ValidationError("Request must be approved by manager first.")

        leave_request.status = LeaveRequest.StatusChoice.APPROVED
        leave_request.hr_approved_by_id = hr_id
        leave_request.hr_approved_at = timezone.now()
        leave_request.save()

        # Balance avtomatik ayiriladi
        from apps.hris.leave_management.services.leave_balance_services import LeaveBalanceService
        LeaveBalanceService.deduct_balance(
            employee_id=leave_request.employee_id,
            leave_type_id=leave_request.leave_type_id,
            year=leave_request.start_date.year,
            days=leave_request.duration,
        )

        LeaveActivityLog.objects.create(
            leave_request=leave_request,
            performed_by_id=hr_id,
            action=LeaveActivityLog.ActionChoice.APPROVED,
            note="HR Director approved",
        )

        logger.info(f"HR approved leave request: id={leave_request_id}, hr_id={hr_id}")
        return leave_request

    @staticmethod
    @transaction.atomic
    def decline(
        leave_request_id: int,
        declined_by_id: int,
        reason: str,
    ) -> LeaveRequest:
        """
        Rad etish — istalgan bosqichda.
        Reason majburiy!
        """
        if not reason or not reason.strip():
            raise ValidationError("Decline reason is required.")

        leave_request = LeaveRequest.objects.filter(
            id=leave_request_id, is_deleted=False
        ).first()

        if not leave_request:
            raise ValueError("Leave request not found.")

        if leave_request.status not in [
            LeaveRequest.StatusChoice.PENDING,
            LeaveRequest.StatusChoice.MANAGER_APPROVED,
        ]:
            raise ValidationError("Only Pending or Manager Approved requests can be declined.")

        leave_request.status = LeaveRequest.StatusChoice.DECLINED
        leave_request.decline_reason = reason
        leave_request.declined_by_id = declined_by_id
        leave_request.declined_at = timezone.now()
        leave_request.save()

        LeaveActivityLog.objects.create(
            leave_request=leave_request,
            performed_by_id=declined_by_id,
            action=LeaveActivityLog.ActionChoice.DECLINED,
            note=reason,
        )

        logger.info(f"Leave request declined: id={leave_request_id}")
        return leave_request

    @staticmethod
    @transaction.atomic
    def interrupt(
        leave_request_id: int,
        interrupted_by_id: int,
        interruption_date,
    ) -> LeaveRequest:
        """
        Ta'tildagi xodimni to'xtatish (Interruption).
        Faqat APPROVED va sana ta'til davri ichida bo'lsa.
        """
        leave_request = LeaveRequest.objects.filter(
            id=leave_request_id, is_deleted=False
        ).first()

        if not leave_request:
            raise ValueError("Leave request not found.")

        if leave_request.status != LeaveRequest.StatusChoice.APPROVED:
            raise ValidationError("Only approved requests can be interrupted.")

        today = timezone.now().date()
        if not (leave_request.start_date <= today <= leave_request.end_date):
            raise ValidationError("Interruption is only allowed during an active leave period.")

        if not (leave_request.start_date <= interruption_date <= leave_request.end_date):
            raise ValidationError("Interruption date must fall within the approved leave period.")

        # Ishlatilmagan kunlarni qaytaramiz
        used_days = (interruption_date - leave_request.start_date).days
        remaining_days = leave_request.duration - used_days

        leave_request.status = LeaveRequest.StatusChoice.INTERRUPTED
        leave_request.interrupted_by_id = interrupted_by_id
        leave_request.interruption_date = interruption_date
        leave_request.interrupted_at = timezone.now()
        leave_request.save()

        # Ishlatilmagan kunlarni balansga qaytaramiz
        if remaining_days > 0:
            from apps.hris.leave_management.services.leave_balance_service import LeaveBalanceService
            LeaveBalanceService.refund_balance(
                employee_id=leave_request.employee_id,
                leave_type_id=leave_request.leave_type_id,
                year=leave_request.start_date.year,
                days=remaining_days,
            )

        LeaveActivityLog.objects.create(
            leave_request=leave_request,
            performed_by_id=interrupted_by_id,
            action=LeaveActivityLog.ActionChoice.INTERRUPTED,
            note=f"Interrupted on {interruption_date}. {remaining_days} days refunded.",
        )

        logger.info(f"Leave request interrupted: id={leave_request_id}, date={interruption_date}")
        return leave_request

    @staticmethod
    @transaction.atomic
    def bulk_approve(
        leave_request_ids: list,
        approved_by_id: int,
        step: str = "manager",  # "manager" yoki "hr"
    ) -> dict:
        """
        Bir vaqtda ko'p so'rovlarni tasdiqlash.
        """
        results = {"approved": [], "failed": []}

        for request_id in leave_request_ids:
            try:
                if step == "manager":
                    LeaveApprovalService.manager_approve(request_id, approved_by_id)
                else:
                    LeaveApprovalService.hr_approve(request_id, approved_by_id)
                results["approved"].append(request_id)
            except Exception as e:
                results["failed"].append({"id": request_id, "error": str(e)})

        return results

    @staticmethod
    @transaction.atomic
    def bulk_decline(
        leave_request_ids: list,
        declined_by_id: int,
        reason: str,
    ) -> dict:
        """
        Bir vaqtda ko'p so'rovlarni rad etish.
        """
        results = {"declined": [], "failed": []}

        for request_id in leave_request_ids:
            try:
                LeaveApprovalService.decline(request_id, declined_by_id, reason)
                results["declined"].append(request_id)
            except Exception as e:
                results["failed"].append({"id": request_id, "error": str(e)})

        return results

    # -------------------------------------------------------
    # Private helper
    # -------------------------------------------------------
    @staticmethod
    def _get_pending_request(leave_request_id: int) -> LeaveRequest:
        leave_request = LeaveRequest.objects.filter(
            id=leave_request_id, is_deleted=False
        ).first()
        if not leave_request:
            raise ValueError("Leave request not found.")
        return leave_request