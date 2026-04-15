from rest_framework import serializers
from django.contrib.auth import get_user_model
from ...models import (
    HiringRequest, HiringRequestApproval, JobAdvertisement,
    Candidate, JobApplication, Interview, CandidateDocument,
    JobOffer, Onboarding, PostProbationEvaluation
)
from apps.audit.models import ActivityLog

User = get_user_model()


def _user_display_name(user):
    """
    Return the best available display name for a user.
    CustomUser has a `full_name` CharField; fall back to username.
    """
    if user is None:
        return None
    return getattr(user, "full_name", None) or user.get_full_name() or user.username


def _candidate_full_name(candidate):
    """
    Candidate has first_name + last_name, no full_name field.
    """
    if candidate is None:
        return None
    return f"{candidate.first_name} {candidate.last_name}".strip()


class HiringRequestApprovalSerializer(serializers.ModelSerializer):
    # Use SerializerMethodField — approver is nullable and CustomUser.full_name
    # is the correct field (not get_full_name() which returns first+last).
    approver_name = serializers.SerializerMethodField()

    class Meta:
        model = HiringRequestApproval
        fields = ["id", "approver", "approver_name", "role_type", "status", "note", "action_at", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_approver_name(self, obj):
        return _user_display_name(obj.approver)


class HiringRequestSerializer(serializers.ModelSerializer):
    approvals = HiringRequestApprovalSerializer(many=True, read_only=True)
    # CustomUser.full_name is a CharField — direct attribute access is correct.
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    job_title_name = serializers.CharField(source="job_title.title", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = HiringRequest
        fields = [
            "id", "company", "job_title", "job_title_name", "department", "department_name",
            "vacancies", "purpose", "status", "created_by", "created_by_name", "approvals",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "created_by", "created_at", "updated_at"]

    def validate_vacancies(self, value):
        if value < 1:
            raise serializers.ValidationError("Vacancies must be at least 1.")
        return value

    def validate_purpose(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Purpose cannot be blank.")
        return value


class HiringRequestUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for PATCH/PUT on a Hiring Request.
    Only exposes the fields that are safe to edit (draft state only).
    Status, company, created_by are never writable via update.
    """
    class Meta:
        model = HiringRequest
        fields = ["job_title", "department", "vacancies", "purpose"]

    def validate_vacancies(self, value):
        if value < 1:
            raise serializers.ValidationError("Vacancies must be at least 1.")
        return value

    def validate_purpose(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Purpose cannot be blank.")
        return value


class JobAdvertisementSerializer(serializers.ModelSerializer):
    job_title_name = serializers.CharField(source="hiring_request.job_title.title", read_only=True)
    department_name = serializers.CharField(source="hiring_request.department.name", read_only=True)

    class Meta:
        model = JobAdvertisement
        fields = [
            "id", "hiring_request", "title", "job_title_name", "department_name",
            "description", "requirements", "skills", "responsibilities",
            "city", "area", "deadline", "platforms",
            "status", "published_at", "closed_at", "created_at",
        ]
        read_only_fields = ["id", "status", "published_at", "closed_at", "created_at"]

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def validate_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Skills must be a list.")
        return value

    def validate_platforms(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Platforms must be a list.")
        return value


class JobAdvertisementUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for PATCH/PUT on a Job Advertisement.

    - DRAFT: all content fields are writable.
    - PUBLISHED: only deadline and platforms are writable (enforced in the service).
    - CLOSED: no updates allowed (enforced in the service).
    """
    class Meta:
        model = JobAdvertisement
        fields = [
            "title", "description", "requirements", "skills",
            "responsibilities", "city", "area", "deadline", "platforms",
        ]

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def validate_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Skills must be a list.")
        return value

    def validate_platforms(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Platforms must be a list.")
        return value


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = [
            "id", "first_name", "last_name", "email", "phone",
            "linkedin_url", "photo", "cv_file", "source", "company", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class JobApplicationSerializer(serializers.ModelSerializer):
    candidate_details = CandidateSerializer(source="candidate", read_only=True)
    job_title = serializers.CharField(source="job_advertisement.title", read_only=True)

    class Meta:
        model = JobApplication
        fields = [
            "id", "candidate", "candidate_details", "job_advertisement", "job_title",
            "status", "classification", "job_board", "applied_at", "notes",
        ]
        read_only_fields = ["id", "applied_at"]

    def validate_job_board(self, value):
        if value:
            valid = [c[0] for c in JobApplication.JobBoardSource.choices]
            if value not in valid:
                raise serializers.ValidationError(
                    f"Invalid job_board '{value}'. Must be one of: {valid}"
                )
        return value


class InterviewerScoreSerializer(serializers.Serializer):
    interviewer_id = serializers.IntegerField()
    score = serializers.FloatField(min_value=0, max_value=10)
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_interviewer_id(self, value):
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"User with id {value} does not exist.")
        return value


class InterviewSerializer(serializers.ModelSerializer):
    interviewer_names = serializers.SerializerMethodField()
    # Candidate has first_name + last_name, no full_name field — use method.
    candidate_name = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = [
            "id", "application", "candidate_name", "interview_type",
            "interview_date", "status", "call_status", "interviewers", "interviewer_names",
            "average_score", "scoring_data", "note", "created_at",
        ]
        read_only_fields = ["id", "average_score", "created_at"]

    def get_candidate_name(self, obj):
        return _candidate_full_name(obj.application.candidate)

    def get_interviewer_names(self, obj):
        return [_user_display_name(u) for u in obj.interviewers.all()]

    def validate_scoring_data(self, value):
        if isinstance(value, list):
            s = InterviewerScoreSerializer(data=value, many=True)
            s.is_valid(raise_exception=True)
        return value


class CandidateDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateDocument
        fields = ["id", "candidate", "doc_type", "file", "status", "note", "created_at"]
        read_only_fields = ["id", "created_at"]


class JobOfferSerializer(serializers.ModelSerializer):
    # Candidate has no full_name — use method.
    candidate_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source="application.job_advertisement.title", read_only=True)

    class Meta:
        model = JobOffer
        fields = [
            "id", "application", "candidate_name", "job_title",
            "salary", "allowance", "benefits", "start_date", "offer_validity_date",
            "status", "responded_at", "note", "created_at",
        ]
        read_only_fields = ["id", "status", "responded_at", "created_at"]

    def get_candidate_name(self, obj):
        return _candidate_full_name(obj.application.candidate)

    def validate(self, data):
        start = data.get("start_date") or (self.instance.start_date if self.instance else None)
        validity = data.get("offer_validity_date") or (
            self.instance.offer_validity_date if self.instance else None
        )
        if start and validity and validity < start:
            raise serializers.ValidationError(
                {"offer_validity_date": "offer_validity_date must be on or after start_date."}
            )
        return data


class OnboardingSerializer(serializers.ModelSerializer):
    # Candidate has no full_name — use method.
    candidate_name = serializers.SerializerMethodField()

    class Meta:
        model = Onboarding
        fields = [
            "id", "candidate", "candidate_name", "tasks", "status",
            "session_date", "session_location", "assigned_mentor",
            "attended", "engagement_level", "survey_link", "survey_responses",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_candidate_name(self, obj):
        return _candidate_full_name(obj.candidate)

    def validate_engagement_level(self, value):
        if value is not None and not (1 <= value <= 5):
            raise serializers.ValidationError("engagement_level must be between 1 and 5.")
        return value


class ApprovalFlowSerializer(serializers.ModelSerializer):
    approver_name = serializers.SerializerMethodField()

    class Meta:
        model = HiringRequestApproval
        fields = ["id", "role_type", "approver", "approver_name", "status", "action_at", "note", "created_at"]
        read_only_fields = ["id", "role_type", "approver", "approver_name", "status", "action_at", "note", "created_at"]

    def get_approver_name(self, obj):
        return _user_display_name(obj.approver)


class ImportErrorSerializer(serializers.Serializer):
    row = serializers.IntegerField()
    error = serializers.CharField()


class ImportSummarySerializer(serializers.Serializer):
    added = serializers.IntegerField()
    shortlist_1 = serializers.IntegerField()
    shortlist_2 = serializers.IntegerField()
    rejected = serializers.IntegerField()
    errors = ImportErrorSerializer(many=True)
    imported_at = serializers.DateTimeField()


class SyncResultSerializer(serializers.Serializer):
    synced = serializers.IntegerField()
    skipped_duplicates = serializers.IntegerField()
    platforms_attempted = serializers.ListField(child=serializers.CharField())
    synced_at = serializers.DateTimeField()


class ActivityLogSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.SerializerMethodField()
    performed_by_id = serializers.IntegerField(source="user_id", read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)
    details = serializers.JSONField(source="new_values", read_only=True)

    class Meta:
        model = ActivityLog
        ref_name = "RecruitmentActivityLog"
        fields = [
            "id", "action", "entity_type", "entity_id",
            "performed_by_name", "performed_by_id", "timestamp", "details",
        ]
        read_only_fields = fields

    def get_performed_by_name(self, obj):
        return _user_display_name(obj.user)


class PostProbationEvaluationSerializer(serializers.ModelSerializer):
    evaluated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PostProbationEvaluation
        fields = [
            "id", "application",
            "evaluation_date", "performance_score", "decision", "comments",
            "tasks_score", "attendance_score", "initiative_score",
            "collaboration_score", "teamwork_score", "average_score",
            "evaluated_by", "evaluated_by_name", "workflow_status",
            "manager_note", "hr_note", "rationale",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "average_score", "workflow_status", "created_at", "updated_at"]

    def get_evaluated_by_name(self, obj):
        return _user_display_name(obj.evaluated_by)

    def validate_tasks_score(self, value):
        if value is not None and not (1 <= value <= 5):
            raise serializers.ValidationError("Score must be between 1 and 5.")
        return value

    def validate_attendance_score(self, value):
        if value is not None and not (1 <= value <= 5):
            raise serializers.ValidationError("Score must be between 1 and 5.")
        return value

    def validate_initiative_score(self, value):
        if value is not None and not (1 <= value <= 5):
            raise serializers.ValidationError("Score must be between 1 and 5.")
        return value

    def validate_collaboration_score(self, value):
        if value is not None and not (1 <= value <= 5):
            raise serializers.ValidationError("Score must be between 1 and 5.")
        return value

    def validate_teamwork_score(self, value):
        if value is not None and not (1 <= value <= 5):
            raise serializers.ValidationError("Score must be between 1 and 5.")
        return value
