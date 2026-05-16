"""
Exit Interview Service / Chiqish Suhbati Xizmati

Schedule and conduct exit interviews
Chiqish suhbatlarini rejalashtirish va o'tkazish
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.hris.termination.models import ExitInterview, TerminationRequest
from apps.audit.services import log_activity


class ExitInterviewService:
    """
    Service for managing exit interviews
    Chiqish suhbatlarini boshqarish xizmati
    """

    @staticmethod
    @transaction.atomic
    def schedule_exit_interview(
            termination_request,
            scheduled_date,
            scheduled_by,
            interview_method='in_person',
            location=None
    ):
        """
        Schedule an exit interview
        Chiqish suhbatini rejalashtirish

        Args:
            termination_request: TerminationRequest object
            scheduled_date: When to conduct interview
            scheduled_by: HR scheduling
            interview_method: in_person, video_call, phone, or written
            location: Office location or video call link

        Returns:
            ExitInterview object
        """

        # Check if exit interview already exists
        # Chiqish suhbati allaqachon mavjudligini tekshirish
        if hasattr(termination_request, 'exit_interview'):
            raise ValidationError(
                f"Exit interview already scheduled for this termination (ID: {termination_request.exit_interview.id})"
            )

        # Validate scheduled date is before final working day
        # Rejalashtirilgan sana yakuniy ish kunidan oldin ekanligini tekshirish
        if termination_request.final_working_day:
            if scheduled_date.date() >= termination_request.final_working_day:
                raise ValidationError(
                    "Exit interview must be scheduled before final working day"
                )

        # Deceased employees don't need exit interviews
        # Vafot etgan xodimlarga chiqish suhbati kerak emas
        if termination_request.termination_type == TerminationRequest.TerminationType.DECEASED:
            raise ValidationError(
                "Exit interview not required for deceased employees"
            )

        # Create exit interview
        # Chiqish suhbatini yaratish
        exit_interview = ExitInterview.objects.create(
            termination_request=termination_request,
            employee=termination_request.employee,
            status=ExitInterview.Status.SCHEDULED,
            scheduled_date=scheduled_date,
            interview_method=interview_method,
            location=location or ""
        )

        # Log activity
        log_activity(
            user=scheduled_by,
            action="EXIT_INTERVIEW_SCHEDULED",
            model_name="ExitInterview",
            object_id=exit_interview.id,
            changes={
                "employee": termination_request.employee.full_name,
                "scheduled_date": str(scheduled_date),
                "interview_method": interview_method
            }
        )

        return exit_interview

    @staticmethod
    @transaction.atomic
    def conduct_exit_interview(
            exit_interview,
            conducted_by,
            primary_reason,
            reason_details=None,
            overall_satisfaction=None,
            job_satisfaction=None,
            manager_satisfaction=None,
            team_satisfaction=None,
            compensation_satisfaction=None,
            work_environment_satisfaction=None,
            what_did_you_like=None,
            what_to_improve=None,
            would_recommend=None,
            would_return=None,
            additional_comments=None,
            hr_notes=None,
            action_items=None
    ):
        """
        Conduct and complete exit interview
        Chiqish suhbatini o'tkazish va yakunlash

        Args:
            exit_interview: ExitInterview object
            conducted_by: HR conducting interview
            primary_reason: Main reason for leaving
            reason_details: Detailed explanation
            overall_satisfaction: 1-5 rating
            ... (other satisfaction ratings)
            what_did_you_like: What employee liked most
            what_to_improve: Suggestions for improvement
            would_recommend: Would recommend company?
            would_return: Would consider returning?
            additional_comments: Any additional feedback
            hr_notes: Internal HR notes
            action_items: Actions to take based on feedback

        Returns:
            Updated ExitInterview
        """

        # Validate status
        # Holatni tekshirish
        if exit_interview.status != ExitInterview.Status.SCHEDULED:
            raise ValidationError(
                f"Can only conduct scheduled interviews. Current: {exit_interview.get_status_display()}"
            )

        # Validate primary reason
        # Asosiy sababni tekshirish
        valid_reasons = [
            'better_opportunity',
            'salary',
            'career_growth',
            'work_life_balance',
            'management',
            'work_environment',
            'location',
            'personal',
            'retirement',
            'health',
            'relocation',
            'other'
        ]

        if primary_reason not in valid_reasons:
            raise ValidationError(
                f"Invalid primary reason. Must be one of: {valid_reasons}"
            )

        # Validate satisfaction ratings (1-5)
        # Qoniqish reytinglarini tekshirish (1-5)
        satisfaction_fields = [
            overall_satisfaction,
            job_satisfaction,
            manager_satisfaction,
            team_satisfaction,
            compensation_satisfaction,
            work_environment_satisfaction
        ]

        for rating in satisfaction_fields:
            if rating is not None and not (1 <= rating <= 5):
                raise ValidationError(
                    "Satisfaction ratings must be between 1 and 5"
                )

        # Update exit interview
        # Chiqish suhbatini yangilash
        exit_interview.status = ExitInterview.Status.COMPLETED
        exit_interview.conducted_by = conducted_by
        exit_interview.primary_reason = primary_reason
        exit_interview.reason_details = reason_details or ""

        # Satisfaction ratings
        # Qoniqish reyting


lari
exit_interview.overall_satisfaction = overall_satisfaction
exit_interview.job_satisfaction = job_satisfaction
exit_interview.manager_satisfaction = manager_satisfaction
exit_interview.team_satisfaction = team_satisfaction
exit_interview.compensation_satisfaction = compensation_satisfaction
exit_interview.work_environment_satisfaction = work_environment_satisfaction

# Open-ended feedback
# Ochiq javob
exit_interview.what_did_you_like = what_did_you_like or ""
exit_interview.what_to_improve = what_to_improve or ""
exit_interview.would_recommend = would_recommend
exit_interview.would_return = would_return
exit_interview.additional_comments = additional_comments or ""

# HR internal
# HR ichki
exit_interview.hr_notes = hr_notes or ""
exit_interview.action_items = action_items or ""

exit_interview.save()

# Log activity
log_activity(
    user=conducted_by,
    action="EXIT_INTERVIEW_COMPLETED",
    model_name="ExitInterview",
    object_id=exit_interview.id,
    changes={
        "employee": exit_interview.employee.full_name,
        "conducted_date": str(exit_interview.conducted_date),
        "primary_reason": primary_reason,
        "overall_satisfaction": overall_satisfaction,
        "would_recommend": would_recommend
    }
)

return exit_interview


@staticmethod
@transaction.atomic
def reschedule_exit_interview(
        exit_interview,
        new_scheduled_date,
        rescheduled_by,
        reschedule_reason,
        new_location=None
):
    """
    Reschedule an exit interview
    Chiqish suhbatini qayta rejalashtirish

    Args:
        exit_interview: ExitInterview object
        new_scheduled_date: New date/time
        rescheduled_by: HR rescheduling
        reschedule_reason: Reason for rescheduling
        new_location: Optional new location

    Returns:
        Updated ExitInterview
    """

    # Validate status
    # Holatni tekshirish
    if exit_interview.status != ExitInterview.Status.SCHEDULED:
        raise ValidationError(
            f"Can only reschedule scheduled interviews. Current: {exit_interview.get_status_display()}"
        )

    # Validate new date is before final working day
    # Yangi sana yakuniy ish kunidan oldin ekanligini tekshirish
    if exit_interview.termination_request.final_working_day:
        if new_scheduled_date.date() >= exit_interview.termination_request.final_working_day:
            raise ValidationError(
                "Exit interview must be scheduled before final working day"
            )

    # Update exit interview
    # Chiqish suhbatini yangilash
    old_date = exit_interview.scheduled_date
    exit_interview.scheduled_date = new_scheduled_date

    if new_location:
        exit_interview.location = new_location

    # Add rescheduling note to HR notes
    # Qayta rejalashtirishni HR eslatmalariga qo'shish
    reschedule_note = f"\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] Rescheduled by {rescheduled_by.full_name}: {reschedule_reason}\nOld Date: {old_date}"
    exit_interview.hr_notes = (exit_interview.hr_notes or "") + reschedule_note

    exit_interview.save()

    # Log activity
    log_activity(
        user=rescheduled_by,
        action="EXIT_INTERVIEW_RESCHEDULED",
        model_name="ExitInterview",
        object_id=exit_interview.id,
        changes={
            "employee": exit_interview.employee.full_name,
            "old_date": str(old_date),
            "new_date": str(new_scheduled_date),
            "reason": reschedule_reason
        }
    )

    return exit_interview


@staticmethod
@transaction.atomic
def cancel_exit_interview(exit_interview, cancelled_by, cancellation_reason):
    """
    Cancel an exit interview
    Chiqish suhbatini bekor qilish

    Args:
        exit_interview: ExitInterview object
        cancelled_by: HR cancelling
        cancellation_reason: Reason for cancellation

    Returns:
        Updated ExitInterview
    """

    # Validate status
    # Holatni tekshirish
    if exit_interview.status != ExitInterview.Status.SCHEDULED:
        raise ValidationError(
            f"Can only cancel scheduled interviews. Current: {exit_interview.get_status_display()}"
        )

    if not cancellation_reason:
        raise ValidationError("Cancellation reason is required")

    # Update exit interview
    # Chiqish suhbatini yangilash
    exit_interview.status = ExitInterview.Status.CANCELLED

    # Add cancellation note
    # Bekor qilish eslatmasini qo'shish
    cancellation_note = f"\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] Cancelled by {cancelled_by.full_name}: {cancellation_reason}"
    exit_interview.hr_notes = (exit_interview.hr_notes or "") + cancellation_note

    exit_interview.save()

    # Log activity
    log_activity(
        user=cancelled_by,
        action="EXIT_INTERVIEW_CANCELLED",
        model_name="ExitInterview",
        object_id=exit_interview.id,
        changes={
            "employee": exit_interview.employee.full_name,
            "cancellation_reason": cancellation_reason
        }
    )

    return exit_interview


@staticmethod
@transaction.atomic
def mark_no_show(exit_interview, marked_by, no_show_notes=None):
    """
    Mark exit interview as no-show
    Chiqish suhbatini kelmagan deb belgilash

    Args:
        exit_interview: ExitInterview object
        marked_by: HR marking
        no_show_notes: Optional notes

    Returns:
        Updated ExitInterview
    """

    # Validate status
    # Holatni tekshirish
    if exit_interview.status != ExitInterview.Status.SCHEDULED:
        raise ValidationError(
            f"Can only mark scheduled interviews as no-show. Current: {exit_interview.get_status_display()}"
        )

    # Validate interview time has passed
    # Suhbat vaqti o'tganligini tekshirish
    if timezone.now() < exit_interview.scheduled_date:
        raise ValidationError(
            "Cannot mark as no-show before scheduled time"
        )

    # Update exit interview
    # Chiqish suhbatini yangilash
    exit_interview.status = ExitInterview.Status.NO_SHOW

    # Add no-show note
    # Kelmagan eslatmasini qo'shish
    no_show_note = f"\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] Marked as no-show by {marked_by.full_name}"
    if no_show_notes:
        no_show_note += f": {no_show_notes}"
    exit_interview.hr_notes = (exit_interview.hr_notes or "") + no_show_note

    exit_interview.save()

    # Log activity
    log_activity(
        user=marked_by,
        action="EXIT_INTERVIEW_NO_SHOW",
        model_name="ExitInterview",
        object_id=exit_interview.id,
        changes={
            "employee": exit_interview.employee.full_name,
            "scheduled_date": str(exit_interview.scheduled_date)
        }
    )

    return exit_interview