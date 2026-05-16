"""
Exit Interview Model

Captures feedback from departing employees to improve workplace.
Conducted before final working day.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.models import TimeStampedModel, SoftDeleteModel


class ExitInterview(TimeStampedModel, SoftDeleteModel):
    """
    Exit interview conducted with departing employees.

    Purpose:
    - Gather feedback on work environment
    - Understand reasons for leaving
    - Identify areas for improvement
    - Document employee experience
    """

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", _("Scheduled")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")
        NO_SHOW = "no_show", _("No Show")

    # Satisfaction ratings (1-5 scale)
    class SatisfactionLevel(models.IntegerChoices):
        VERY_DISSATISFIED = 1, _("Very Dissatisfied")
        DISSATISFIED = 2, _("Dissatisfied")
        NEUTRAL = 3, _("Neutral")
        SATISFIED = 4, _("Satisfied")
        VERY_SATISFIED = 5, _("Very Satisfied")

    # Core fields
    termination_request = models.OneToOneField(
        "TerminationRequest",
        on_delete=models.CASCADE,
        related_name="exit_interview",
        verbose_name=_("Termination Request")
    )

    employee = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.CASCADE,
        related_name="exit_interviews",
        verbose_name=_("Employee")
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        verbose_name=_("Status")
    )

    # Scheduling
    scheduled_date = models.DateTimeField(
        verbose_name=_("Scheduled Date"),
        help_text=_("Must be before final working day")
    )

    conducted_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Conducted Date")
    )

    conducted_by = models.ForeignKey(
        "hris_core.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conducted_exit_interviews",
        verbose_name=_("Conducted By"),
        help_text=_("HR Manager conducting the interview")
    )

    # Interview location/method
    interview_method = models.CharField(
        max_length=20,
        choices=[
            ("in_person", _("In Person")),
            ("video_call", _("Video Call")),
            ("phone", _("Phone")),
            ("written", _("Written Form"))
        ],
        default="in_person",
        verbose_name=_("Interview Method")
    )

    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Location"),
        help_text=_("Office location or video call link")
    )

    # Primary reason for leaving
    primary_reason = models.CharField(
        max_length=50,
        choices=[
            ("better_opportunity", _("Better Opportunity")),
            ("salary", _("Salary/Compensation")),
            ("career_growth", _("Career Growth")),
            ("work_life_balance", _("Work-Life Balance")),
            ("management", _("Management Issues")),
            ("work_environment", _("Work Environment")),
            ("location", _("Location/Commute")),
            ("personal", _("Personal Reasons")),
            ("retirement", _("Retirement")),
            ("health", _("Health Reasons")),
            ("relocation", _("Relocation")),
            ("other", _("Other"))
        ],
        blank=True,
        verbose_name=_("Primary Reason for Leaving")
    )

    # Detailed feedback
    reason_details = models.TextField(
        blank=True,
        verbose_name=_("Reason Details"),
        help_text=_("Detailed explanation")
    )

    # Satisfaction ratings
    overall_satisfaction = models.IntegerField(
        choices=SatisfactionLevel.choices,
        null=True,
        blank=True,
        verbose_name=_("Overall Satisfaction")
    )

    job_satisfaction = models.IntegerField(
        choices=SatisfactionLevel.choices,
        null=True,
        blank=True,
        verbose_name=_("Job Satisfaction")
    )

    manager_satisfaction = models.IntegerField(
        choices=SatisfactionLevel.choices,
        null=True,
        blank=True,
        verbose_name=_("Manager Satisfaction")
    )

    team_satisfaction = models.IntegerField(
        choices=SatisfactionLevel.choices,
        null=True,
        blank=True,
        verbose_name=_("Team Satisfaction")
    )

    compensation_satisfaction = models.IntegerField(
        choices=SatisfactionLevel.choices,
        null=True,
        blank=True,
        verbose_name=_("Compensation Satisfaction")
    )

    work_environment_satisfaction = models.IntegerField(
        choices=SatisfactionLevel.choices,
        null=True,
        blank=True,
        verbose_name=_("Work Environment Satisfaction")
    )

    # Open-ended questions
    what_did_you_like = models.TextField(
        blank=True,
        verbose_name=_("What Did You Like Most?")
    )

    what_to_improve = models.TextField(
        blank=True,
        verbose_name=_("What Should Be Improved?")
    )

    would_recommend = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_("Would Recommend Company?"),
        help_text=_("Would you recommend this company to others?")
    )

    would_return = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_("Would Consider Returning?"),
        help_text=_("Would you consider working here again?")
    )

    # Additional comments
    additional_comments = models.TextField(
        blank=True,
        verbose_name=_("Additional Comments")
    )

    # HR notes (internal)
    hr_notes = models.TextField(
        blank=True,
        verbose_name=_("HR Notes"),
        help_text=_("Internal notes for HR review")
    )

    # Action items
    action_items = models.TextField(
        blank=True,
        verbose_name=_("Action Items"),
        help_text=_("Improvements or actions to take based on feedback")
    )

    # Privacy
    is_confidential = models.BooleanField(
        default=True,
        verbose_name=_("Is Confidential"),
        help_text=_("Keep interview details confidential")
    )

    class Meta:
        db_table = "hris_exit_interviews"
        ordering = ["-scheduled_date"]
        indexes = [
            models.Index(fields=["employee", "status"]),
            models.Index(fields=["scheduled_date"]),
            models.Index(fields=["primary_reason"]),
        ]
        verbose_name = _("Exit Interview")
        verbose_name_plural = _("Exit Interviews")

    def __str__(self):
        return f"Exit Interview - {self.employee.full_name} ({self.scheduled_date.date()})"

    def clean(self):
        """Validation rules"""
        super().clean()

        # Scheduled date must be before final working day
        if (self.termination_request.final_working_day
            and self.scheduled_date.date() >= self.termination_request.final_working_day):
            raise ValidationError({
                "scheduled_date": _("Exit interview must be scheduled before final working day")
            })

        # Conducted date must be after or equal to scheduled date
        if self.conducted_date and self.conducted_date < self.scheduled_date:
            raise ValidationError({
                "conducted_date": _("Conducted date cannot be before scheduled date")
            })

        # If status is COMPLETED, must have conducted_date and conducted_by
        if self.status == self.Status.COMPLETED:
            if not self.conducted_date:
                raise ValidationError({
                    "conducted_date": _("Conducted date required for completed interviews")
                })
            if not self.conducted_by:
                raise ValidationError({
                    "conducted_by": _("Conducted by required for completed interviews")
                })

    def save(self, *args, **kwargs):
        """Auto-set fields on save"""

        # Auto-set employee from termination request
        if not self.employee_id:
            self.employee = self.termination_request.employee

        # Set conducted_date when status changes to COMPLETED
        if self.status == self.Status.COMPLETED and not self.conducted_date:
            self.conducted_date = timezone.now()

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def average_satisfaction(self):
        """Calculate average satisfaction across all ratings"""
        ratings = [
            self.overall_satisfaction,
            self.job_satisfaction,
            self.manager_satisfaction,
            self.team_satisfaction,
            self.compensation_satisfaction,
            self.work_environment_satisfaction
        ]

        # Filter out None values
        valid_ratings = [r for r in ratings if r is not None]

        if not valid_ratings:
            return None

        return round(sum(valid_ratings) / len(valid_ratings), 2)

    @property
    def is_overdue(self):
        """Check if scheduled interview is overdue"""
        if self.status != self.Status.SCHEDULED:
            return False

        return timezone.now() > self.scheduled_date