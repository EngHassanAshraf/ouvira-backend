from rest_framework import serializers
from django.contrib.auth import get_user_model
from ...models import (
    HiringRequest, HiringRequestApproval, JobAdvertisement,
    Candidate, JobApplication, Interview, CandidateDocument,
    JobOffer, Onboarding
)

User = get_user_model()


class HiringRequestApprovalSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source="approver.get_full_name", read_only=True)

    class Meta:
        model = HiringRequestApproval
        fields = ["id", "approver", "approver_name", "role_type", "status", "note", "action_at", "created_at"]
        read_only_fields = ["id", "created_at"]


class HiringRequestSerializer(serializers.ModelSerializer):
    approvals = HiringRequestApprovalSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
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

    The serializer accepts all editable fields; the service enforces
    state-based restrictions so the error message is business-meaningful.
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
        fields = ["id", "first_name", "last_name", "email", "phone", "linkedin_url", "photo", "cv_file", "source", "company", "created_at"]
        read_only_fields = ["id", "created_at"]


class JobApplicationSerializer(serializers.ModelSerializer):
    candidate_details = CandidateSerializer(source="candidate", read_only=True)
    job_title = serializers.CharField(source="job_advertisement.title", read_only=True)

    class Meta:
        model = JobApplication
        fields = ["id", "candidate", "candidate_details", "job_advertisement", "job_title", "status", "classification", "applied_at", "notes"]
        read_only_fields = ["id", "applied_at"]


class InterviewSerializer(serializers.ModelSerializer):
    interviewer_names = serializers.SerializerMethodField()
    candidate_name = serializers.CharField(source="application.candidate.full_name", read_only=True)

    class Meta:
        model = Interview
        fields = [
            "id", "application", "candidate_name", "interview_type",
            "interview_date", "status", "interviewers", "interviewer_names",
            "average_score", "scoring_data", "note", "created_at",
        ]
        read_only_fields = ["id", "average_score", "created_at"]

    def get_interviewer_names(self, obj):
        return [user.get_full_name() or user.username for user in obj.interviewers.all()]


class CandidateDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateDocument
        fields = ["id", "candidate", "doc_type", "file", "status", "note", "created_at"]
        read_only_fields = ["id", "created_at"]


class JobOfferSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source="application.candidate.full_name", read_only=True)
    job_title = serializers.CharField(source="application.job_advertisement.title", read_only=True)

    class Meta:
        model = JobOffer
        fields = [
            "id", "application", "candidate_name", "job_title",
            "salary", "allowance", "benefits", "start_date",
            "status", "responded_at", "note", "created_at",
        ]
        read_only_fields = ["id", "status", "responded_at", "created_at"]


class OnboardingSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)

    class Meta:
        model = Onboarding
        fields = ["id", "candidate", "candidate_name", "tasks", "status", "created_at"]
        read_only_fields = ["id", "created_at"]
