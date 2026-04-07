import logging
from django.db import transaction
from django.utils import timezone
from apps.audit.services.activity_log_service import ActivityLogService
from apps.audit.utils import get_or_create_date_dim
from ...models import Interview, JobApplication

logger = logging.getLogger(__name__)

class InterviewService:
    """
    Service for managing Interviews and Evaluator feedback.
    """

    @staticmethod
    @transaction.atomic
    def schedule_interview(application_id, interview_type, interview_date, interviewers):
        """
        Schedules a new interview for a job application.
        """
        application = JobApplication.objects.get(id=application_id)
        
        interview = Interview.objects.create(
            application=application,
            interview_type=interview_type,
            interview_date=interview_date,
            status=Interview.Status.SCHEDULED
        )
        
        if interviewers:
            interview.interviewers.set(interviewers)

        # Log Activity
        ActivityLogService.log_activity(
            user=None, # TBD: who is scheduling
            company=application.job_advertisement.hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="Interview",
            entity_id=interview.id,
            action=f"SCHEDULED_{interview_type.upper()}"
        )

        return interview

    @staticmethod
    @transaction.atomic
    def record_interview_result(interview_id, user, scoring_data, note=None):
        """
        Records the scoring and feedback for a completed interview.
        Calculates the average score based on the metrics provided.
        """
        interview = Interview.objects.select_for_update().get(id=interview_id)
        
        # Calculate Average Score from scoring_data (e.g. {"tasks": 8, "ethics": 9})
        scores = [v for k, v in scoring_data.items() if isinstance(v, (int, float))]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        interview.scoring_data = scoring_data
        interview.average_score = round(avg_score, 2)
        interview.note = note
        interview.status = Interview.Status.COMPLETED
        interview.save()

        # Log Activity
        ActivityLogService.log_activity(
            user=user,
            company=interview.application.job_advertisement.hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="Interview",
            entity_id=interview.id,
            action="COMPLETED",
            new_values={"scoring_data": scoring_data, "avg_score": avg_score}
        )

        return interview
