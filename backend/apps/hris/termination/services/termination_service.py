"""
Termination Service / Ishdan Bo'shatish Xizmati

Company-initiated terminations
Kompaniya tomonidan ishdan bo'shatish
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from apps.hris.termination.models import TerminationRequest
from apps.audit.services import log_activity


class TerminationService:
    """
    Service for company-initiated terminations
    Kompaniya tomonidan ishdan bo'shatish xizmati
    """

    @staticmethod
    @transaction.atomic
    def initiate_behavioral_termination(
            employee,
            violation_description,
            initiated_by,
            is_gross_violation=False,
            attachment=None
    ):
        """
        Initiate termination for behavioral violation
        Xulq-atvor buzilishi uchun ishdan bo'shatishni boshlash

        Args:
            employee: Employee being terminated / Ishdan bo'shatilayotgan xodim
            violation_description: Detailed violation description / Batafsil buzilish tavsifi
            initiated_by: HR initiating / Boshlovchi HR
            is_gross_violation: True for immediate termination / To'g'ridan-to'g'ri tugatish uchun True
            attachment: Evidence/documentation / Dalil/hujjat

        Returns:
            TerminationRequest object
        """

        # Check for active termination
        # Faol tugatish mavjudligini tekshirish
        active_termination = TerminationRequest.objects.filter(
            employee=employee,
            status__in=[
                TerminationRequest.Status.SUBMITTED,
                TerminationRequest.Status.MANAGER_APPROVED,
                TerminationRequest.Status.GM_APPROVED
            ]
        ).first()

        if active_termination:
            raise ValidationError(
                f"Employee already has an active termination request (ID: {active_termination.id})"
            )

        # Determine notice period
        # Ogohlik muddatini aniqlash
        if is_gross_violation:
            # Immediate termination for gross violations
            # Og'ir buzilishlar uchun to'g'ridan-to'g'ri tugatish
            notice_period_days = 0
            final_working_day = timezone.now().date()
        else:
            # Standard notice period
            # Standart ogohlik muddati
            notice_period_days = 30
            final_working_day = timezone.now().date() + timedelta(days=30)

        # Create termination request
        # Tugatish so'rovini yaratish
        termination = TerminationRequest.objects.create(
            employee=employee,
            termination_type=TerminationRequest.TerminationType.BEHAVIORAL,
            status=TerminationRequest.Status.SUBMITTED,
            reason=violation_description,
            is_voluntary=False,
            notice_period_days=notice_period_days,
            final_working_day=final_working_day,
            requested_by=initiated_by,
            attachment=attachment
        )

        # Log activity
        log_activity(
            user=initiated_by,
            action="BEHAVIORAL_TERMINATION_INITIATED",
            model_name="TerminationRequest",
            object_id=termination.id,
            changes={
                "employee": employee.full_name,
                "is_gross_violation": is_gross_violation,
                "final_working_day": str(final_working_day)
            }
        )

        return termination

    @staticmethod
    @transaction.atomic
    def initiate_performance_termination(
            employee,
            performance_issues,
            initiated_by,
            evaluation_scores=None,
            attachment=None
    ):
        """
        Initiate termination for poor performance
        Yomon ish faoliyati uchun ishdan bo'shatishni boshlash

        Note: Should have prior performance warnings
        Izoh: Oldingi ish faoliyati ogohlantirishlari bo'lishi kerak

        Args:
            employee: Employee being terminated
            performance_issues: Detailed performance issues
            initiated_by: HR initiating
            evaluation_scores: Optional list of evaluation scores
            attachment: Performance evaluation documents

        Returns:
            TerminationRequest object
        """

        # Create termination request
        # Tugatish so'rovini yaratish
        termination = TerminationRequest.objects.create(
            employee=employee,
            termination_type=TerminationRequest.TerminationType.PERFORMANCE,
            status=TerminationRequest.Status.SUBMITTED,
            reason=performance_issues,
            is_voluntary=False,
            notice_period_days=30,
            final_working_day=timezone.now().date() + timedelta(days=30),
            requested_by=initiated_by,
            attachment=attachment
        )

        # Add evaluation scores to notes if provided
        # Taqdim etilgan bo'lsa baholash balllarini eslatmalarga qo'shish
        if evaluation_scores:
            termination.notes = f"Evaluation Scores: {evaluation_scores}"
            termination.save()

        # Log activity
        log_activity(
            user=initiated_by,
            action="PERFORMANCE_TERMINATION_INITIATED",
            model_name="TerminationRequest",
            object_id=termination.id,
            changes={
                "employee": employee.full_name,
                "evaluation_scores": evaluation_scores,
                "final_working_day": str(termination.final_working_day)
            }
        )

        return termination

    @staticmethod
    @transaction.atomic
    def initiate_probation_termination(
            employee,
            probation_reason,
            initiated_by,
            attachment=None
    ):
        """
        Initiate termination during probation period
        Sinov muddati davomida ishdan bo'shatishni boshlash

        Note: Either party can terminate without notice during probation (3-6 months)
        Izoh: Har ikki tomon sinov muddatida ogohlantirishsiz tugatishi mumkin (3-6 oy)

        Args:
            employee: Employee being terminated
            probation_reason: Reason for probation termination
            initiated_by: HR initiating
            attachment: Optional documentation

        Returns:
            TerminationRequest object
        """

        # TODO: Check if employee is actually in probation period
        # TODO: Xodim haqiqatan ham sinov muddatida ekanligini tekshirish

        # Probation termination has no notice period
        # Sinov muddatida tugatish ogohlik muddatiga ega emas
        termination = TerminationRequest.objects.create(
            employee=employee,
            termination_type=TerminationRequest.TerminationType.PROBATION,
            status=TerminationRequest.Status.SUBMITTED,
            reason=probation_reason,
            is_voluntary=False,
            notice_period_days=0,
            final_working_day=timezone.now().date(),
            requested_by=initiated_by,
            attachment=attachment
        )

        # Log activity
        log_activity(
            user=initiated_by,
            action="PROBATION_TERMINATION_INITIATED",
            model_name="TerminationRequest",
            object_id=termination.id,
            changes={
                "employee": employee.full_name,
                "final_working_day": str(termination.final_working_day)
            }
        )

        return termination

    @staticmethod
    @transaction.atomic
    def initiate_medical_termination(
            employee,
            medical_condition,
            is_reassignment_possible,
            initiated_by,
            medical_reports=None
    ):
        """
        Initiate termination for medical reasons
        Tibbiy sabablarga ko'ra ishdan bo'shatishni boshlash

        Note: Consider reassignment to suitable position first
        Izoh: Avval mos lavozimga o'tkazishni ko'rib chiqing

        Args:
            employee: Employee being terminated
            medical_condition: Medical condition description
            is_reassignment_possible: Can employee be reassigned to another role?
            initiated_by: HR initiating
            medical_reports: Medical documentation

        Returns:
            TerminationRequest object
        """

        # Build reason with reassignment consideration
        # Qayta tayinlashni hisobga olgan holda sababni qurish
        reason = f"Medical Condition: {medical_condition}\n"

        if is_reassignment_possible:
            reason += "Reassignment to suitable position should be considered before termination."
        else:
            reason += "No suitable position available for reassignment."

        # Create termination request
        # Tugatish so'rovini yaratish
        termination = TerminationRequest.objects.create(
            employee=employee,
            termination_type=TerminationRequest.TerminationType.MEDICAL,
            status=TerminationRequest.Status.SUBMITTED,
            reason=reason,
            is_voluntary=False,
            notice_period_days=30,
            final_working_day=timezone.now().date() + timedelta(days=30),
            requested_by=initiated_by,
            attachment=medical_reports
        )

        # Log activity
        log_activity(
            user=initiated_by,
            action="MEDICAL_TERMINATION_INITIATED",
            model_name="TerminationRequest",
            object_id=termination.id,
            changes={
                "employee": employee.full_name,
                "is_reassignment_possible": is_reassignment_possible,
                "final_working_day": str(termination.final_working_day)
            }
        )

        return termination

    @staticmethod
    @transaction.atomic
    def initiate_layoff(
            employee,
            layoff_reason,
            initiated_by,
            department_restructuring=False,
            economic_downturn=False,
            attachment=None
    ):
        """
        Initiate layoff (restructuring/economic reasons)
        Qisqartirishni boshlash (qayta tuzish/iqtisodiy sabablar)

        Note: Provide proper notice and severance package
        Izoh: To'g'ri ogohlik va tugatish to'lovi paketini taqdim eting

        Args:
            employee: Employee being laid off
            layoff_reason: Detailed reason for layoff
            initiated_by: HR initiating
            department_restructuring: True if due to restructuring
            economic_downturn: True if due to economic reasons
            attachment: Optional documentation

        Returns:
            TerminationRequest object
        """

        # Build detailed reason
        # Batafsil sabab qurish
        reason = f"Layoff Reason: {layoff_reason}\n"

        if department_restructuring:
            reason += "- Department Restructuring\n"
        if economic_downturn:
            reason += "- Economic Downturn\n"

        # Layoffs typically have extended notice period
        # Qisqartirish odatda uzoq ogohlik muddatiga ega
        notice_period_days = 60

        # Create termination request
        # Tugatish so'rovini yaratish
        termination = TerminationRequest.objects.create(
            employee=employee,
            termination_type=TerminationRequest.TerminationType.LAYOFF,
            status=TerminationRequest.Status.SUBMITTED,
            reason=reason,
            is_voluntary=False,
            notice_period_days=notice_period_days,
            final_working_day=timezone.now().date() + timedelta(days=notice_period_days),
            requested_by=initiated_by,
            attachment=attachment
        )

        # Log activity
        log_activity(
            user=initiated_by,
            action="LAYOFF_INITIATED",
            model_name="TerminationRequest",
            object_id=termination.id,
            changes={
                "employee": employee.full_name,
                "department_restructuring": department_restructuring,
                "economic_downturn": economic_downturn,
                "notice_period_days": notice_period_days
            }
        )

        return termination

    @staticmethod
    @transaction.atomic
    def process_deceased_employee(
            employee,
            date_of_death,
            initiated_by,
            next_of_kin_name=None,
            next_of_kin_relationship=None,
            next_of_kin_contact=None,
            death_certificate=None
    ):
        """
        Process termination for deceased employee
        Vafot etgan xodim uchun tugatishni qayta ishlash

        Note: Settlement paid to legal heir within 1 week
        Izoh: To'lov qonuniy merosxo'rga 1 hafta ichida to'lanadi

        Args:
            employee: Deceased employee
            date_of_death: Date of death
            initiated_by: HR processing
            next_of_kin_name: Legal heir name
            next_of_kin_relationship: Relationship (spouse, child, parent)
            next_of_kin_contact: Contact information
            death_certificate: Death certificate document

        Returns:
            TerminationRequest object
        """

        # Build reason with next of kin details
        # Merosxo'r tafsilotlari bilan sabab qurish
        reason = f"Employee deceased on {date_of_death}\n"

        if next_of_kin_name:
            reason += f"\nNext of Kin: {next_of_kin_name}"
            if next_of_kin_relationship:
                reason += f" ({next_of_kin_relationship})"
            if next_of_kin_contact:
                reason += f"\nContact: {next_of_kin_contact}"

        # Create termination request
        # Tugatish so'rovini yaratish
        termination = TerminationRequest.objects.create(
            employee=employee,
            termination_type=TerminationRequest.TerminationType.DECEASED,
            status=TerminationRequest.Status.GM_APPROVED,  # Auto-approved for deceased
            reason=reason,
            is_voluntary=False,
            notice_period_days=0,
            final_working_day=date_of_death,
            requested_by=initiated_by,
            approved_by_gm=initiated_by,  # HR can auto-approve deceased cases
            gm_approval_date=timezone.now(),
            attachment=death_certificate
        )

        # Log activity
        log_activity(
            user=initiated_by,
            action="DECEASED_EMPLOYEE_PROCESSED",
            model_name="TerminationRequest",
            object_id=termination.id,
            changes={
                "employee": employee.full_name,
                "date_of_death": str(date_of_death),
                "next_of_kin": next_of_kin_name
            }
        )

        return termination

    @staticmethod
    @transaction.atomic
    def process_termination(termination, processed_by):
        """
        Mark termination as processed (final step after settlement & exit interview)
        Tugatishni qayta ishlangan deb belgilash (to'lov va chiqish suhbatidan keyin yakuniy qadam)

        Args:
            termination: TerminationRequest object
            processed_by: HR processing

        Returns:
            Updated TerminationRequest
        """

        # Validate status
        # Holatni tekshirish
        if termination.status != TerminationRequest.Status.GM_APPROVED:
            raise ValidationError(
                f"Can only process GM-approved terminations. Current: {termination.get_status_display()}"
            )

        # Check if exit interview completed (if required)
        # Chiqish suhbati tugallanganligini tekshirish (agar talab qilinsa)
        if termination.requires_exit_interview:
            if not hasattr(termination, 'exit_interview'):
                raise ValidationError(
                    "Exit interview must be conducted before processing termination"
                )

            if termination.exit_interview.status != 'completed':
                raise ValidationError(
                    "Exit interview must be completed before processing termination"
                )

        # Check if settlement is paid
        # To'lov to'langanligini tekshirish
        if hasattr(termination, 'settlement'):
            if termination.settlement.status != 'paid':
                raise ValidationError(
                    "Settlement must be paid before processing termination"
                )

        # Update termination
        # Tugatishni yangilash
        termination.status = TerminationRequest.Status.PROCESSED
        termination.processed_by = processed_by
        termination.save()

        # Log activity
        log_activity(
            user=processed_by,
            action="TERMINATION_PROCESSED",
            model_name="TerminationRequest",
            object_id=termination.id,
            changes={
                "employee": termination.employee.full_name,
                "processed_date": str(termination.processed_date),
                "termination_type": termination.get_termination_type_display()
            }
        )

        return termination