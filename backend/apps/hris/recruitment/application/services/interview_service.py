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
    def record_interview_result(interview_id, user, scoring_data, note=None, call_status=None):
        """
        Records the scoring and feedback for a completed interview.

        scoring_data can be:
        - List format (new): [{"interviewer_id": 1, "score": 8.0, "note": "..."}]
        - Dict format (legacy): {"tasks": 8, "ethics": 9}

        average_score is auto-computed from the scores.
        """
        interview = Interview.objects.select_for_update().get(id=interview_id)

        # Compute average score
        if isinstance(scoring_data, list):
            # New structured format: list of {interviewer_id, score, note}
            scores = [
                entry["score"] for entry in scoring_data
                if isinstance(entry, dict) and "score" in entry
            ]
        else:
            # Legacy dict format: {metric_name: score_value}
            scores = [v for v in scoring_data.values() if isinstance(v, (int, float))]

        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        interview.scoring_data = scoring_data
        interview.average_score = avg_score
        interview.note = note
        interview.status = Interview.Status.COMPLETED

        if call_status is not None:
            interview.call_status = call_status

        interview.save()

        ActivityLogService.log_activity(
            user=user,
            company=interview.application.job_advertisement.hiring_request.company,
            date_dim=get_or_create_date_dim(timezone.now().date()),
            entity_type="Interview",
            entity_id=interview.id,
            action="COMPLETED",
            new_values={"avg_score": avg_score, "call_status": call_status}
        )

        return interview
