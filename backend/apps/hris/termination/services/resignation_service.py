"""
Resignation Service / Iste'fo Xizmati

Employee resignation submission and withdrawal
Xodim iste'fosi va uni qaytarib olish
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from apps.hris.termination.models import TerminationRequest
from apps.audit.services import log_activity


class ResignationService:
    """
    Service for handling employee resignations
    Xodim iste'folari bilan ishlash xizmati
    """

    @staticmethod
    @transaction.atomic
    def submit_resignation(employee, reason, notice_period_days=30, attachment=None, requested_by=None):
        """
        Submit a resignation request
        Iste'fo so'rovini yuborish

        Args:
            employee: Employee who is resigning / Iste'fo berayotgan xodim
            reason: Reason for resignation / Iste'fo sababi
            notice_period_days: Notice period in days / Ogohlik muddati (kunlarda)
            attachment: Optional resignation letter / Ixtiyoriy iste'fo xati
            requested_by: Who submitted (employee or manager on behalf)

        Returns:
            TerminationRequest object / TerminationRequest obyekti
        """

        # Check if employee already has active resignation
        # Xodimda faol iste'fo borligini tekshirish
        active_resignation = TerminationRequest.objects.filter(
            employee=employee,
            termination_type=TerminationRequest.TerminationType.RESIGNATION,
            status__in=[
                TerminationRequest.Status.DRAFT,
                TerminationRequest.Status.SUBMITTED,
                TerminationRequest.Status.MANAGER_APPROVED,
                TerminationRequest.Status.GM_APPROVED
            ]
        ).first()

        if active_resignation:
            raise ValidationError(
                f"Employee already has an active resignation (Status: {active_resignation.get_status_display()})"
            )

        # Create resignation request
        # Iste'fo so'rovini yaratish
        resignation = TerminationRequest.objects.create(
            employee=employee,
            termination_type=TerminationRequest.TerminationType.RESIGNATION,
            status=TerminationRequest.Status.SUBMITTED,
            reason=reason,
            is_voluntary=True,
            notice_period_days=notice_period_days,
            requested_by=requested_by or employee,
            attachment=attachment
        )

        # Auto-calculate final working day (30 days from submission)
        # Yakuniy ish kunini avtomatik hisoblash (topshirilgan kundan 30 kun)
        resignation.final_working_day = resignation.submission_date + timedelta(days=notice_period_days)
        resignation.save()

        # Log activity
        log_activity(
            user=requested_by or employee,
            action="RESIGNATION_SUBMITTED",
            model_name="TerminationRequest",
            object_id=resignation.id,
            changes={
                "employee": employee.full_name,
                "submission_date": str(resignation.submission_date),
                "final_working_day": str(resignation.final_working_day)
            }
        )

        return resignation

    @staticmethod
    @transaction.atomic
    def withdraw_resignation(resignation, employee, withdrawal_reason):
        """
        Withdraw a resignation request (within 7 days)
        Iste'foni qaytarib olish (7 kun ichida)

        Args:
            resignation: TerminationRequest object
            employee: Employee withdrawing
            withdrawal_reason: Reason for withdrawal

        Returns:
            Updated TerminationRequest
        """

        # Validate employee owns this resignation
        # Xodim bu iste'foga egaligini tekshirish
        if resignation.employee != employee:
            raise ValidationError("You can only withdraw your own resignation")

        # Check if resignation type is correct
        # Iste'fo turini tekshirish
        if resignation.termination_type != TerminationRequest.TerminationType.RESIGNATION:
            raise ValidationError("Only resignations can be withdrawn")

        # Check if resignation can be withdrawn (within 7 days)
        # Iste'foni qaytarib olish mumkinligini tekshirish (7 kun ichida)
        if not resignation.can_be_withdrawn:
            raise ValidationError(
                "Resignation can only be withdrawn within 7 working days of submission"
            )

        # Check status
        # Holatni tekshirish
        if resignation.status not in [
            TerminationRequest.Status.SUBMITTED,
            TerminationRequest.Status.MANAGER_APPROVED
        ]:
            raise ValidationError(
                f"Cannot withdraw resignation with status: {resignation.get_status_display()}"
            )

        # Update resignation status
        # Iste'fo holatini yangilash
        resignation.status = TerminationRequest.Status.WITHDRAWN
        resignation.withdrawal_request_date = timezone.now()
        resignation.withdrawal_reason = withdrawal_reason
        resignation.save()

        # Log activity
        log_activity(
            user=employee,
            action="RESIGNATION_WITHDRAWN",
            model_name="TerminationRequest",
            object_id=resignation.id,
            changes={
                "employee": employee.full_name,
                "withdrawal_date": str(resignation.withdrawal_request_date),
                "withdrawal_reason": withdrawal_reason
            }
        )

        return resignation

    @staticmethod
    @transaction.atomic
    def manager_approve_resignation(resignation, manager, notes=None):
        """
        Manager approval of resignation (Step 1)
        Menejer tomonidan iste'foni tasdiqlash (1-qadam)

        Args:
            resignation: TerminationRequest object
            manager: Manager approving
            notes: Optional manager notes

        Returns:
            Updated TerminationRequest
        """

        # Validate status
        # Holatni tekshirish
        if resignation.status != TerminationRequest.Status.SUBMITTED:
            raise ValidationError(
                f"Can only approve resignations in SUBMITTED status. Current: {resignation.get_status_display()}"
            )

        # Validate termination type
        # Tugatish turini tekshirish
        if resignation.termination_type != TerminationRequest.TerminationType.RESIGNATION:
            raise ValidationError("This is not a resignation request")

        # Check if manager has permission
        # Menejer ruxsatini tekshirish
        # TODO: Add permission check - manager should be employee's manager
        # TODO: Ruxsat tekshiruvini qo'shish - menejer xodimning menederi bo'lishi kerak

        # Update resignation
        # Iste'foni yangilash
        resignation.status = TerminationRequest.Status.MANAGER_APPROVED
        resignation.approved_by_manager = manager
        resignation.manager_approval_date = timezone.now()

        if notes:
            resignation.notes = (resignation.notes or "") + f"\n\nManager Notes: {notes}"

        resignation.save()

        # Log activity
        log_activity(
            user=manager,
            action="RESIGNATION_MANAGER_APPROVED",
            model_name="TerminationRequest",
            object_id=resignation.id,
            changes={
                "employee": resignation.employee.full_name,
                "approved_by": manager.full_name,
                "approval_date": str(resignation.manager_approval_date)
            }
        )

        return resignation

    @staticmethod
    @transaction.atomic
    def gm_approve_resignation(resignation, gm, notes=None):
        """
        GM (General Manager) final approval of resignation (Step 2)
        Bosh direktor tomonidan yakuniy tasdiqlash (2-qadam)

        Args:
            resignation: TerminationRequest object
            gm: General Manager approving
            notes: Optional GM notes

        Returns:
            Updated TerminationRequest
        """

        # Validate status
        # Holatni tekshirish
        if resignation.status != TerminationRequest.Status.MANAGER_APPROVED:
            raise ValidationError(
                f"Can only GM approve resignations in MANAGER_APPROVED status. Current: {resignation.get_status_display()}"
            )

        # Validate termination type
        # Tugatish turini tekshirish
        if resignation.termination_type != TerminationRequest.TerminationType.RESIGNATION:
            raise ValidationError("This is not a resignation request")

        # Check if GM has permission
        # GM ruxsatini tekshirish
        # TODO: Add permission check - user should have GM role
        # TODO: Ruxsat tekshiruvini qo'shish - foydalanuvchi GM roliga ega bo'lishi kerak

        # Update resignation
        # Iste'foni yangilash
        resignation.status = TerminationRequest.Status.GM_APPROVED
        resignation.approved_by_gm = gm
        resignation.gm_approval_date = timezone.now()

        if notes:
            resignation.notes = (resignation.notes or "") + f"\n\nGM Notes: {notes}"

        resignation.save()

        # Log activity
        log_activity(
            user=gm,
            action="RESIGNATION_GM_APPROVED",
            model_name="TerminationRequest",
            object_id=resignation.id,
            changes={
                "employee": resignation.employee.full_name,
                "approved_by": gm.full_name,
                "approval_date": str(resignation.gm_approval_date),
                "final_working_day": str(resignation.final_working_day)
            }
        )

        return resignation

    @staticmethod
    @transaction.atomic
    def reject_resignation(resignation, rejected_by, rejection_reason):
        """
        Reject a resignation request
        Iste'foni rad etish

        Args:
            resignation: TerminationRequest object
            rejected_by: Manager/GM rejecting
            rejection_reason: Reason for rejection

        Returns:
            Updated TerminationRequest
        """

        # Validate status
        # Holatni tekshirish
        if resignation.status not in [
            TerminationRequest.Status.SUBMITTED,
            TerminationRequest.Status.MANAGER_APPROVED
        ]:
            raise ValidationError(
                f"Cannot reject resignation with status: {resignation.get_status_display()}"
            )

        if not rejection_reason:
            raise ValidationError("Rejection reason is required")

        # Update resignation
        # Iste'foni yangilash
        resignation.status = TerminationRequest.Status.REJECTED
        resignation.rejected_by = rejected_by
        resignation.rejection_date = timezone.now()
        resignation.rejection_reason = rejection_reason
        resignation.save()

        # Log activity
        log_activity(
            user=rejected_by,
            action="RESIGNATION_REJECTED",
            model_name="TerminationRequest",
            object_id=resignation.id,
            changes={
                "employee": resignation.employee.full_name,
                "rejected_by": rejected_by.full_name,
                "rejection_reason": rejection_reason
            }
        )

        return resignation