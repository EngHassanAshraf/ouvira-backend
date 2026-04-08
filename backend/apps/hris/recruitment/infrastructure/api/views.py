from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import (
    HiringRequestSerializer,
    HiringRequestApprovalSerializer,
    JobAdvertisementSerializer,
    CandidateSerializer,
    JobApplicationSerializer,
    InterviewSerializer,
    CandidateDocumentSerializer,
    JobOfferSerializer,
    OnboardingSerializer,
)

from ...models import (
    HiringRequest,
    HiringRequestApproval,
    JobAdvertisement,
    Candidate,
    JobApplication,
    Interview,
    CandidateDocument,
    JobOffer,
    Onboarding,
)
from ...application.services.hiring_request_service import HiringRequestService
from ...application.services.job_advertisement_service import JobAdvertisementService
from ...application.services.application_service import ApplicationService
from ...application.services.interview_service import InterviewService
from ...application.services.document_service import DocumentService
from ...application.services.job_offer_service import JobOfferService
from ...infrastructure.persistence.selectors import (
    get_hiring_requests_for_company,
    get_advertisements_for_company,
    get_candidates_for_company,
    get_applications_for_company,
    get_interviews_for_application,
    get_documents_for_candidate,
    get_offers_for_company,
)


def _company_id(request):
    """Helper: resolve company_id from query param or tenant."""
    return (
        request.query_params.get("company")
        or getattr(request.user, "company_id", None)
        or getattr(getattr(request, "tenant", None), "id", None)
    )


# ─── Hiring Request ────────────────────────────────────────────────────────────

class HiringRequestViewSet(viewsets.ModelViewSet):
    """Full CRUD + workflow actions for Hiring Requests."""
    serializer_class = HiringRequestSerializer
    queryset = HiringRequest.objects.all()

    def get_queryset(self):
        cid = _company_id(self.request)
        if cid:
            return get_hiring_requests_for_company(cid)
        return super().get_queryset().select_related(
            "job_title", "department", "created_by"
        ).prefetch_related("approvals")

    def perform_create(self, serializer):
        serializer.instance = HiringRequestService.create_hiring_request(
            user=self.request.user,
            company=serializer.validated_data["company"],
            data=serializer.validated_data,
        )

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        try:
            obj = HiringRequestService.submit_hiring_request(pk, request.user)
            return Response(self.get_serializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        role_type = request.data.get("role_type")
        if not role_type:
            return Response({"detail": "role_type is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            obj = HiringRequestService.approve_request(
                pk, request.user, role_type, request.data.get("note", "")
            )
            return Response(self.get_serializer(obj).data)
        except (ValueError, HiringRequestApproval.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        role_type = request.data.get("role_type")
        reason = request.data.get("reason")
        if not role_type or not reason:
            return Response(
                {"detail": "role_type and reason are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            obj = HiringRequestService.reject_request(pk, request.user, role_type, reason)
            return Response(self.get_serializer(obj).data)
        except (ValueError, HiringRequestApproval.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ─── Job Advertisement ─────────────────────────────────────────────────────────

class JobAdvertisementViewSet(viewsets.ModelViewSet):
    """CRUD + publish/close actions for Job Advertisements."""
    serializer_class = JobAdvertisementSerializer
    queryset = JobAdvertisement.objects.all()

    def get_queryset(self):
        cid = _company_id(self.request)
        status_filter = self.request.query_params.get("status")
        if cid:
            return get_advertisements_for_company(cid, status=status_filter)
        return super().get_queryset().select_related(
            "hiring_request__job_title", "hiring_request__department"
        )

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        try:
            obj = JobAdvertisementService.publish_advertisement(pk, request.user, request.data)
            return Response(self.get_serializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        try:
            obj = JobAdvertisementService.close_advertisement(pk, request.user)
            return Response(self.get_serializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ─── Candidate ─────────────────────────────────────────────────────────────────

class CandidateViewSet(viewsets.ModelViewSet):
    """CRUD for Candidates, with optional name/email search."""
    serializer_class = CandidateSerializer
    queryset = Candidate.objects.all()

    def get_queryset(self):
        cid = _company_id(self.request)
        search = self.request.query_params.get("search")
        if cid:
            return get_candidates_for_company(cid, search=search)
        return super().get_queryset()


# ─── Job Application (Kanban) ──────────────────────────────────────────────────

class JobApplicationViewSet(viewsets.ModelViewSet):
    """CRUD + move-to-stage action for the Kanban pipeline."""
    serializer_class = JobApplicationSerializer
    queryset = JobApplication.objects.all()

    def get_queryset(self):
        cid = _company_id(self.request)
        status_filter = self.request.query_params.get("status")
        if cid:
            return get_applications_for_company(cid, status=status_filter)
        return super().get_queryset().select_related("candidate", "job_advertisement")

    @action(detail=True, methods=["post"], url_path="move-to-stage")
    def move_to_stage(self, request, pk=None):
        new_status = request.data.get("status")
        if not new_status:
            return Response({"detail": "status is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            obj = ApplicationService.move_to_stage(
                pk, new_status, request.user, request.data.get("classification")
            )
            return Response(self.get_serializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ─── Interview ─────────────────────────────────────────────────────────────────

class InterviewViewSet(viewsets.ModelViewSet):
    """CRUD + record-result action for Interviews."""
    serializer_class = InterviewSerializer
    queryset = Interview.objects.all()

    def get_queryset(self):
        application_id = self.request.query_params.get("application")
        if application_id:
            return get_interviews_for_application(application_id)
        cid = _company_id(self.request)
        qs = super().get_queryset().select_related(
            "application", "application__candidate"
        ).prefetch_related("interviewers")
        if cid:
            qs = qs.filter(application__candidate__company_id=cid)
        return qs

    def perform_create(self, serializer):
        interviewers = self.request.data.get("interviewers", [])
        serializer.instance = InterviewService.schedule_interview(
            application_id=serializer.validated_data["application"].id,
            interview_type=serializer.validated_data["interview_type"],
            interview_date=serializer.validated_data["interview_date"],
            interviewers=[int(i) for i in interviewers] if interviewers else [],
        )

    @action(detail=True, methods=["post"], url_path="record-result")
    def record_result(self, request, pk=None):
        scoring = request.data.get("scoring_data")
        if not scoring:
            return Response({"detail": "scoring_data is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            obj = InterviewService.record_interview_result(
                pk, request.user, scoring, request.data.get("note")
            )
            return Response(self.get_serializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ─── Candidate Document ────────────────────────────────────────────────────────

class CandidateDocumentViewSet(viewsets.ModelViewSet):
    """CRUD + verify action for Candidate Documents."""
    serializer_class = CandidateDocumentSerializer
    queryset = CandidateDocument.objects.all()

    def get_queryset(self):
        candidate_id = self.request.query_params.get("candidate")
        if candidate_id:
            return get_documents_for_candidate(candidate_id)
        cid = _company_id(self.request)
        qs = super().get_queryset()
        if cid:
            qs = qs.filter(candidate__company_id=cid)
        return qs

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        doc_status = request.data.get("status")
        if not doc_status:
            return Response({"detail": "status is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            obj = DocumentService.verify_document(
                pk, doc_status, request.user, request.data.get("note")
            )
            return Response(self.get_serializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ─── Job Offer ─────────────────────────────────────────────────────────────────

class JobOfferViewSet(viewsets.ModelViewSet):
    """CRUD + accept/decline actions for Job Offers."""
    serializer_class = JobOfferSerializer
    queryset = JobOffer.objects.all()

    def get_queryset(self):
        cid = _company_id(self.request)
        if cid:
            return get_offers_for_company(cid)
        return super().get_queryset().select_related(
            "application__candidate", "application__job_advertisement"
        )

    def perform_create(self, serializer):
        serializer.instance = JobOfferService.create_offer(
            application_id=serializer.validated_data["application"].id,
            offer_data=serializer.validated_data,
        )

    @action(detail=True, methods=["post"], url_path="accept")
    def accept(self, request, pk=None):
        """Final Decision: accept offer and create Employee in hris_core."""
        required = ["employee_id", "national_id"]
        missing = [f for f in required if not request.data.get(f)]
        if missing:
            return Response(
                {"detail": f"Missing required fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            obj = JobOfferService.accept_offer(pk, request.user, request.data)
            return Response(self.get_serializer(obj).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="decline")
    def decline(self, request, pk=None):
        try:
            obj = JobOfferService.decline_offer(pk, request.user, request.data.get("reason"))
            return Response(self.get_serializer(obj).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ─── Onboarding ────────────────────────────────────────────────────────────────

class OnboardingViewSet(viewsets.ModelViewSet):
    """CRUD for Onboarding checklists."""
    serializer_class = OnboardingSerializer
    queryset = Onboarding.objects.all()

    def get_queryset(self):
        cid = _company_id(self.request)
        qs = super().get_queryset().select_related("candidate")
        if cid:
            qs = qs.filter(candidate__company_id=cid)
        return qs
