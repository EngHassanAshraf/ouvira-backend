"""
PostProbationService — manages the multi-step approval workflow
for PostProbationEvaluation.

Workflow:
  draft → submitted_to_manager → manager_approved → hr_confirmed → final_decision
"""
import logging
from django.db import transaction
from django.utils import timezone

from ...models import PostProbationEvaluation

logger = logging.getLogger(__name__)

TRANSITIONS = {
    "draft":                "submitted_to_manager",
    "submitted_to_manager": "manager_approved",
    "manager_approved":     "hr_confirmed",
    "hr_confirmed":         "final_decision",
}


class PostProbationService:

    @staticmethod
    def _get_and_transition(eval_id, expected_status, next_status, **update_fields):
        """
        Fetch evaluation, assert current workflow_status == expected_status,
        update to next_status and apply any extra fields.
        """
        with transaction.atomic():
            evaluation = PostProbationEvaluation.objects.select_for_update().get(pk=eval_id)
            if evaluation.workflow_status != expected_status:
                raise ValueError(
                    f"Cannot transition from '{evaluation.workflow_status}'. "
                    f"Expected status: '{expected_status}'."
                )
            evaluation.workflow_status = next_status
            for field_name, value in update_fields.items():
                setattr(evaluation, field_name, value)
            evaluation.save()
            return evaluation

    @staticmethod
    def submit_to_manager(eval_id, user) -> PostProbationEvaluation:
        """HR submits evaluation to manager for sign-off."""
        return PostProbationService._get_and_transition(
            eval_id,
            expected_status=PostProbationEvaluation.WorkflowStatus.DRAFT,
            next_status=PostProbationEvaluation.WorkflowStatus.SUBMITTED_TO_MANAGER,
            evaluated_by=user,
        )

    @staticmethod
    def manager_approve(eval_id, user, note: str = "") -> PostProbationEvaluation:
        """Manager approves the evaluation."""
        return PostProbationService._get_and_transition(
            eval_id,
            expected_status=PostProbationEvaluation.WorkflowStatus.SUBMITTED_TO_MANAGER,
            next_status=PostProbationEvaluation.WorkflowStatus.MANAGER_APPROVED,
            manager_note=note,
        )

    @staticmethod
    def hr_confirm(eval_id, user, note: str = "") -> PostProbationEvaluation:
        """HR confirms the manager-approved evaluation."""
        return PostProbationService._get_and_transition(
            eval_id,
            expected_status=PostProbationEvaluation.WorkflowStatus.MANAGER_APPROVED,
            next_status=PostProbationEvaluation.WorkflowStatus.HR_CONFIRMED,
            hr_note=note,
        )

    @staticmethod
    def record_decision(eval_id, user, decision: str, rationale: str = "") -> PostProbationEvaluation:
        """Record the final employment decision (confirmed/terminated)."""
        valid_decisions = ["confirmed", "terminated"]
        if decision not in valid_decisions:
            raise ValueError(f"Invalid decision '{decision}'. Must be one of: {valid_decisions}")
        return PostProbationService._get_and_transition(
            eval_id,
            expected_status=PostProbationEvaluation.WorkflowStatus.HR_CONFIRMED,
            next_status=PostProbationEvaluation.WorkflowStatus.FINAL_DECISION,
            decision=decision,
            rationale=rationale,
        )
