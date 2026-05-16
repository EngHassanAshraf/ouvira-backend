"""
Warning Service / Ogohlantirish Xizmati

Issue warnings for absence and performance issues
Davomat va ish faoliyati muammolari uchun ogohlantirish berish
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.hris.termination.models import TerminationWarning, TerminationRequest
from apps.audit.services import log_activity


class WarningService:
    """
    Service for issuing and managing termination warnings
    Ogohlantirish berish va boshqarish xizmati
    """

    @staticmethod
    @transaction.atomic
    def issue_absence_warning(
            employee,
            warning_type,  # ABSENCE_EGYPTIAN or ABSENCE_SAUDI
            absence_start_date,
            absence_days_count,
            reason,
            issued_by,
            sent_via_registered_mail=False,
            registered_mail_tracking=None,
            form_s6_attached=False,
            attachment=None
    ):
        """
        Issue an absence warning (Egyptian or Saudi Labor Law)
        Davomat ogohlantirishini berish (Misr yoki Saudiya mehnat qonuni)

        Args:
            employee: Employee receiving warning / Ogohlantirish olayotgan xodim
            warning_type: ABSENCE_EGYPTIAN or ABSENCE_SAUDI
            absence_start_date: First day of absence / Davomatning birinchi kuni
            absence_days_count: Total absence days / Jami davomat kunlari
            reason: Detailed reason / Batafsil sabab
            issued_by: HR issuing the warning / Ogohlantirish berayotgan HR
            sent_via_registered_mail: True if sent by registered mail (Saudi 2nd warning)
            registered_mail_tracking: Tracking number
            form_s6_attached: True if Form S6 attached (Egyptian Law)
            attachment: Optional attachment file

        Returns:
            TerminationWarning object
        """

        # Determine warning level based on absence days
        # Davomat kunlari asosida ogohlantirish darajasini aniqlash
        if absence_days_count >= 10:
            warning_level = TerminationWarning.WarningLevel.SECOND
        elif absence_days_count >= 5:
            warning_level = TerminationWarning.WarningLevel.FIRST
        else:
            raise ValidationError(
                "Absence warning requires at least 5 days of unexcused absence"
            )

        # Check if previous warnings exist
        # Oldingi ogohlantirishlar mavjudligini tekshirish
        previous_warnings = TerminationWarning.objects.filter(
            employee=employee,
            warning_type=warning_type,
            status__in=[
                TerminationWarning.Status.ISSUED,
                TerminationWarning.Status.ACKNOWLEDGED
            ]
        ).order_by('-issue_date')

        # If issuing 2nd warning, check if 1st warning exists
        # 2-ogohlantirish berilayotgan bo'lsa, 1-ogohlantirish mavjudligini tekshirish
        if warning_level == TerminationWarning.WarningLevel.SECOND:
            first_warning_exists = previous_warnings.filter(
                warning_level=TerminationWarning.WarningLevel.FIRST
            ).exists()

            if not first_warning_exists:
                raise ValidationError(
                    "Cannot issue 2nd warning without a 1st warning"
                )

        # Create warning
        # Ogohlantirish yaratish
        warning = TerminationWarning.objects.create(
            employee=employee,
            warning_type=warning_type,
            warning_level=warning_level,
            status=TerminationWarning.Status.ISSUED,
            reason=reason,
            absence_start_date=absence_start_date,
            absence_days_count=absence_days_count,
            sent_via_registered_mail=sent_via_registered_mail,
            registered_mail_tracking=registered_mail_tracking or "",
            form_s6_attached=form_s6_attached,
            issued_by=issued_by,
            attachment=attachment
        )

        # Log activity
        log_activity(
            user=issued_by,
            action="ABSENCE_WARNING_ISSUED",
            model_name="TerminationWarning",
            object_id=warning.id,
            changes={
                "employee": employee.full_name,
                "warning_type": warning_type,
                "warning_level": warning_level,
                "absence_days": absence_days_count
            }
        )

        return warning

    @staticmethod
    @transaction.atomic
    def issue_performance_warning(
            employee,
            evaluation_score,
            evaluation_period,
            reason,
            issued_by,
            attachment=None
    ):
        """
        Issue a performance warning
        Ish faoliyati ogohlantirishini berish

        Business Rule / Biznes qoidasi:
        - Warning if score < 50% OR two consecutive scores < 60%
        - Agar ball < 50% YOKI ketma-ket ikkita ball < 60%

        Args:
            employee: Employee receiving warning
            evaluation_score: Performance score (0-100)
            evaluation_period: Evaluation period (e.g., "Q1 2025")
            reason: Detailed reason
            issued_by: HR issuing the warning
            attachment: Optional evaluation document

        Returns:
            TerminationWarning object
        """

        # Validate score
        # Ballni tekshirish
        if not (0 <= evaluation_score <= 100):
            raise ValidationError("Evaluation score must be between 0 and 100")

        # Determine warning level
        # Ogohlantirish darajasini aniqlash
        if evaluation_score < 50:
            # Automatic 2nd warning if score < 50%
            # Agar ball < 50% bo'lsa avtomatik 2-ogohlantirish
            warning_level = TerminationWarning.WarningLevel.SECOND
        elif evaluation_score < 60:
            # Check if previous evaluation was also < 60%
            # Oldingi baholash ham < 60% bo'lganini tekshirish
            previous_low_score = TerminationWarning.objects.filter(
                employee=employee,
                warning_type=TerminationWarning.WarningType.PERFORMANCE,
                warning_level=TerminationWarning.WarningLevel.FIRST,
                evaluation_score__lt=60,
                status__in=[
                    TerminationWarning.Status.ISSUED,
                    TerminationWarning.Status.ACKNOWLEDGED
                ]
            ).exists()

            if previous_low_score:
                # Two consecutive scores < 60% → 2nd warning
                # Ketma-ket ikkita ball < 60% → 2-ogohlantirish
                warning_level = TerminationWarning.WarningLevel.SECOND
            else:
                # First time < 60% → 1st warning
                # Birinchi marta < 60% → 1-ogohlantirish
                warning_level = TerminationWarning.WarningLevel.FIRST
        else:
            raise ValidationError(
                "Performance warning only issued for scores < 60%"
            )

        # Create warning
        # Ogohlantirish yaratish
        warning = TerminationWarning.objects.create(
            employee=employee,
            warning_type=TerminationWarning.WarningType.PERFORMANCE,
            warning_level=warning_level,
            status=TerminationWarning.Status.ISSUED,
            reason=reason,
            evaluation_score=evaluation_score,
            evaluation_period=evaluation_period,
            issued_by=issued_by,
            attachment=attachment
        )

        # Log activity
        log_activity(
            user=issued_by,
            action="PERFORMANCE_WARNING_ISSUED",
            model_name="TerminationWarning",
            object_id=warning.id,
            changes={
                "employee": employee.full_name,
                "warning_level": warning_level,
                "evaluation_score": float(evaluation_score),
                "evaluation_period": evaluation_period
            }
        )

        return warning

    @staticmethod
    @transaction.atomic
    def employee_acknowledge_warning(warning, employee, employee_response=None):
        """
        Employee acknowledges warning
        Xodim ogohlantirishni tan oladi

        Args:
            warning: TerminationWarning object
            employee: Employee acknowledging
            employee_response: Optional employee statement

        Returns:
            Updated TerminationWarning
        """

        # Validate employee
        # Xodimni tekshirish
        if warning.employee != employee:
            raise ValidationError("You can only acknowledge your own warnings")

        # Validate status
        # Holatni tekshirish
        if warning.status != TerminationWarning.Status.ISSUED:
            raise ValidationError(
                f"Warning already in status: {warning.get_status_display()}"
            )

        # Update warning
        # Ogohlantirishni yangilash
        warning.status = TerminationWarning.Status.ACKNOWLEDGED
        warning.employee_response = employee_response or ""
        warning.save()

        # Log activity
        log_activity(
            user=employee,
            action="WARNING_ACKNOWLEDGED",
            model_name="TerminationWarning",
            object_id=warning.id,
            changes={
                "employee": employee.full_name,
                "acknowledged_date": str(warning.acknowledged_date)
            }
        )

        return warning

    @staticmethod
    @transaction.atomic
    def resolve_warning(warning, resolved_by, resolution_notes):
        """
        Resolve a warning (issue resolved, no escalation)
        Ogohlantirishni hal qilish (muammo hal qilindi, kuchaytirishsiz)

        Args:
            warning: TerminationWarning object
            resolved_by: HR/Manager resolving
            resolution_notes: How the issue was resolved

        Returns:
            Updated TerminationWarning
        """

        # Validate status
        # Holatni tekshirish
        if warning.status == TerminationWarning.Status.ESCALATED:
            raise ValidationError("Cannot resolve an escalated warning")

        if warning.status == TerminationWarning.Status.RESOLVED:
            raise ValidationError("Warning is already resolved")

        if not resolution_notes:
            raise ValidationError("Resolution notes are required")

        # Update warning
        # Ogohlantirishni yangilash
        warning.status = TerminationWarning.Status.RESOLVED
        warning.resolution_notes = resolution_notes
        warning.save()

        # Log activity
        log_activity(
            user=resolved_by,
            action="WARNING_RESOLVED",
            model_name="TerminationWarning",
            object_id=warning.id,
            changes={
                "employee": warning.employee.full_name,
                "resolved_by": resolved_by.full_name,
                "resolved_date": str(warning.resolved_date)
            }
        )

        return warning

    @staticmethod
    @transaction.atomic
    def escalate_warning_to_termination(warning, escalated_by, termination_reason):
        """
        Escalate final warning to termination
        Yakuniy ogohlantirishni ishdan bo'shatishga kuchaytirish

        Args:
            warning: TerminationWarning object (must be 2nd warning)
            escalated_by: HR escalating
            termination_reason: Detailed termination reason

        Returns:
            Tuple: (Updated TerminationWarning, New TerminationRequest)
        """

        # Validate warning can be escalated
        # Ogohlantirish kuchaytirilishi mumkinligini tekshirish
        if not warning.can_escalate_to_termination:
            raise ValidationError(
                "Only final warnings (2nd level) that are issued can be escalated"
            )

        # Determine termination type based on warning type
        # Ogohlantirish turiga qarab tugatish turini aniqlash
        if warning.warning_type in [
            TerminationWarning.WarningType.ABSENCE_EGYPTIAN,
            TerminationWarning.WarningType.ABSENCE_SAUDI
        ]:
            termination_type = TerminationRequest.TerminationType.ABSENCE
        elif warning.warning_type == TerminationWarning.WarningType.PERFORMANCE:
            termination_type = TerminationRequest.TerminationType.PERFORMANCE
        else:
            raise ValidationError("Unknown warning type")

        # Create termination request
        # Tugatish so'rovini yaratish
        termination = TerminationRequest.objects.create(
            employee=warning.employee,
            termination_type=termination_type,
            status=TerminationRequest.Status.SUBMITTED,
            reason=termination_reason,
            is_voluntary=False,
            requested_by=escalated_by,
            notice_period_days=0,  # Immediate termination for warnings
            final_working_day=timezone.now().date()
        )

        # Update warning
        # Ogohlantirishni yangilash
        warning.status = TerminationWarning.Status.ESCALATED
        warning.escalated_to_termination = termination
        warning.save()

        # Log activity
        log_activity(
            user=escalated_by,
            action="WARNING_ESCALATED_TO_TERMINATION",
            model_name="TerminationWarning",
            object_id=warning.id,
            changes={
                "employee": warning.employee.full_name,
                "termination_id": termination.id,
                "termination_type": termination_type,
                "escalation_date": str(warning.escalation_date)
            }
        )

        return warning, termination