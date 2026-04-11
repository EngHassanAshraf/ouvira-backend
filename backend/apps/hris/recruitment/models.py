from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel, SoftDeleteModel

class HiringRequest(TimeStampedModel, SoftDeleteModel):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        SUBMITTED = "submitted", _("Submitted")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")
    company = models.ForeignKey("company.Company", on_delete=models.CASCADE, related_name="hiring_requests")
    job_title = models.ForeignKey("hris_core.JobTitle", on_delete=models.PROTECT, related_name="hiring_requests")
    department = models.ForeignKey("hris_core.Department", on_delete=models.PROTECT, related_name="hiring_requests")
    vacancies = models.PositiveIntegerField(default=1)
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    class Meta:
        db_table = "hris_recruitment_hiring_requests"
        ordering = ["-created_at"]

class HiringRequestApproval(TimeStampedModel, SoftDeleteModel):
    class ApproverRole(models.TextChoices):
        EMPLOYEE = "employee", _("Employee")
        HR = "hr_employee", _("HR Employee")
        MANAGER = "direct_manager", _("Direct Manager")
    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")
    hiring_request = models.ForeignKey(HiringRequest, on_delete=models.CASCADE, related_name="approvals")
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    role_type = models.CharField(max_length=20, choices=ApproverRole.choices)
    status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    note = models.TextField(blank=True, null=True)
    action_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = "hris_recruitment_hiring_request_approvals"
        ordering = ["created_at"]

class JobAdvertisement(TimeStampedModel, SoftDeleteModel):
    class AdStatus(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")
        CLOSED = "closed", _("Closed")
    hiring_request = models.OneToOneField(HiringRequest, on_delete=models.CASCADE, related_name="advertisement")
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    skills = models.JSONField(default=list)
    responsibilities = models.TextField()
    city = models.CharField(max_length=100, blank=True, null=True)
    area = models.CharField(max_length=100, blank=True, null=True)
    deadline = models.DateField(null=True, blank=True)
    platforms = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=AdStatus.choices, default=AdStatus.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = "hris_recruitment_job_advertisements"
        ordering = ["-created_at"]

class Candidate(TimeStampedModel, SoftDeleteModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    photo = models.ImageField(upload_to="candidates/photos/", blank=True, null=True)
    cv_file = models.FileField(upload_to="candidates/cvs/", blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    company = models.ForeignKey("company.Company", on_delete=models.CASCADE, related_name="candidates")
    class Meta:
        db_table = "hris_recruitment_candidates"

class JobApplication(TimeStampedModel, SoftDeleteModel):
    class AppStatus(models.TextChoices):
        APPLIED = "applied", _("Applied")
        PHONE_SCREENING = "phone_screening", _("Phone Screening")
        INTERVIEW = "interview", _("Interview")
        OFFER = "offer", _("Offer")
        HIRED = "hired", _("Hired")
        REJECTED = "rejected", _("Rejected")
    class Classification(models.TextChoices):
        SHORTLIST_1 = "shortlist_1", _("Shortlist 1")
        SHORTLIST_2 = "shortlist_2", _("Shortlist 2")
        NONE = "none", _("None")
    class JobBoardSource(models.TextChoices):
        LINKEDIN = "linkedin", _("LinkedIn")
        FACEBOOK = "facebook", _("Facebook")
        BAYT = "bayt", _("Bayt")
        RECOMMENDATION = "recommendation", _("Recommendation")
        INTERNAL = "internal", _("Internal")
        OTHER = "other", _("Other")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="applications")
    job_advertisement = models.ForeignKey(JobAdvertisement, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=AppStatus.choices, default=AppStatus.APPLIED)
    classification = models.CharField(max_length=20, choices=Classification.choices, default=Classification.NONE)
    job_board = models.CharField(max_length=100, choices=JobBoardSource.choices, blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    class Meta:
        db_table = "hris_recruitment_job_applications"
        unique_together = ["candidate", "job_advertisement"]

class Interview(TimeStampedModel, SoftDeleteModel):
    class InterviewType(models.TextChoices):
        PHONE = "phone", _("Phone Screening")
        PERSONAL = "personal", _("Personal Interview")
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", _("Scheduled")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")
    class CallStatus(models.TextChoices):
        NOT_ANSWERED = "not_answered", _("Not Answered")
        SUITABLE = "suitable", _("Suitable")
        CALL_BACK = "call_back", _("Call Back")
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name="interviews")
    interview_type = models.CharField(max_length=20, choices=InterviewType.choices, default=InterviewType.PHONE)
    interview_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    call_status = models.CharField(max_length=20, choices=CallStatus.choices, blank=True, null=True)
    interviewers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="interviews_as_interviewer")
    average_score = models.FloatField(default=0.0)
    scoring_data = models.JSONField(default=dict, blank=True)
    note = models.TextField(blank=True, null=True)
    class Meta:
        db_table = "hris_recruitment_interviews"
        ordering = ["-interview_date"]

class CandidateDocument(TimeStampedModel, SoftDeleteModel):
    class DocType(models.TextChoices):
        ID_COPY = "id_copy", _("ID Copy")
        QUALIFICATION = "qualification", _("Qualification Certificate")
        MILITARY_STATUS = "military_status", _("Military Status")
        PERSONAL_PHOTO = "personal_photo", _("Personal Photo")
        POLICE_CLEARANCE = "police_clearance", _("Police Clearance")
        BIRTH_CERTIFICATE = "birth_certificate", _("Birth Certificate")
        OTHER = "other", _("Other")
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending Approval")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=50, choices=DocType.choices)
    file = models.FileField(upload_to="candidates/documents/")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    note = models.TextField(blank=True, null=True)
    class Meta:
        db_table = "hris_recruitment_candidate_documents"
        unique_together = ["candidate", "doc_type"]


class JobOffer(TimeStampedModel, SoftDeleteModel):
    class OfferStatus(models.TextChoices):
        DRAFT = "draft", _("Draft")
        SENT = "sent", _("Sent")
        ACCEPTED = "accepted", _("Accepted")
        DECLINED = "declined", _("Declined")
        CANCELLED = "cancelled", _("Cancelled")

    application = models.OneToOneField(
        JobApplication, 
        on_delete=models.CASCADE, 
        related_name="offer"
    )
    salary = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Base Salary"))
    allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, verbose_name=_("Allowance"))
    benefits = models.TextField(blank=True, null=True, verbose_name=_("Benefits Package"))
    start_date = models.DateField(verbose_name=_("Proposed Start Date"))
    
    offer_validity_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=OfferStatus.choices, 
        default=OfferStatus.DRAFT
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "hris_recruitment_job_offers"
        verbose_name = _("Job Offer")
        verbose_name_plural = _("Job Offers")

    def __str__(self):
        return f"Offer for {self.application.candidate}"


class Onboarding(TimeStampedModel, SoftDeleteModel):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", _("Not Started")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")

    candidate = models.OneToOneField(
        Candidate, 
        on_delete=models.CASCADE, 
        related_name="onboarding"
    )
    # Flexible checklist (e.g. {"workspace": true, "email_created": false})
    tasks = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED
    )
    session_date = models.DateTimeField(null=True, blank=True)
    session_location = models.CharField(max_length=200, blank=True)
    assigned_mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mentored_onboardings",
    )
    attended = models.BooleanField(null=True)
    engagement_level = models.PositiveSmallIntegerField(null=True, blank=True)
    survey_link = models.URLField(blank=True, null=True)
    survey_responses = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "hris_recruitment_onboarding"
        verbose_name = _("Onboarding")


class PostProbationEvaluation(TimeStampedModel, SoftDeleteModel):
    class WorkflowStatus(models.TextChoices):
        DRAFT = "draft", _("Draft")
        SUBMITTED_TO_MANAGER = "submitted_to_manager", _("Submitted to Manager")
        MANAGER_APPROVED = "manager_approved", _("Manager Approved")
        HR_CONFIRMED = "hr_confirmed", _("HR Confirmed")
        FINAL_DECISION = "final_decision", _("Final Decision")

    application = models.OneToOneField(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="post_probation"
    )
    # Evaluated by Manager after 3 months (placeholder)
    evaluation_date = models.DateField()
    performance_score = models.IntegerField(default=0)
    decision = models.CharField(
        max_length=50,
        choices=[("confirmed", "Confirmed"), ("terminated", "Terminated")]
    )
    comments = models.TextField(blank=True, null=True)

    # Score fields
    tasks_score = models.PositiveSmallIntegerField(null=True, blank=True)
    attendance_score = models.PositiveSmallIntegerField(null=True, blank=True)
    initiative_score = models.PositiveSmallIntegerField(null=True, blank=True)
    collaboration_score = models.PositiveSmallIntegerField(null=True, blank=True)
    teamwork_score = models.PositiveSmallIntegerField(null=True, blank=True)

    average_score = models.FloatField(null=True, blank=True)
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluations_as_evaluator",
    )
    workflow_status = models.CharField(
        max_length=30,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.DRAFT,
    )
    manager_note = models.TextField(blank=True)
    hr_note = models.TextField(blank=True)
    rationale = models.TextField(blank=True)

    class Meta:
        db_table = "hris_recruitment_post_probation_evaluations"

    def save(self, *args, **kwargs):
        scores = [s for s in [
            self.tasks_score, self.attendance_score,
            self.initiative_score, self.collaboration_score,
            self.teamwork_score
        ] if s is not None]
        self.average_score = round(sum(scores) / len(scores), 2) if scores else None
        super().save(*args, **kwargs)


# Legacy / Placeholder models
class JobPost(TimeStampedModel, SoftDeleteModel):
    title = models.CharField(max_length=255)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    class Meta:
        db_table = "hris_recruitment_job_posts"

class Applicant(TimeStampedModel, SoftDeleteModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    resume = models.FileField(upload_to="resumes/")
    applied_job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    class Meta:
        db_table = "hris_recruitment_applicants"