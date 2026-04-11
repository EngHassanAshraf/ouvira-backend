from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import (
    HiringRequestSerializer,
    HiringRequestUpdateSerializer,
    HiringRequestApprovalSerializer,
    JobAdvertisementSerializer,
    JobAdvertisementUpdateSerializer,
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
    """Resolve company_id from query param → user attribute → tenant."""
    return (
        request.query_params.get("company")
        or getattr(request.user, "company_id", None)
        or getattr(getattr(request, "tenant", None), "id", None)
    )


# ─── Hiring Request ────────────────────────────────────────────────────────────

class HiringRequestViewSet(viewsets.ModelViewSet):
    """
    Full CRUD + workflow actions for Hiring Requests.

    Lifecycle:
      draft → [submit] → submitted → [approve/reject] → approved | rejected
      draft | submitted → [cancel] → rejected (terminal)

    Edit rules (enforced by service):
      - PUT/PATCH: only allowed on DRAFT requests.
      - DELETE:    only allowed on DRAFT requests (soft delete).
    """
    queryset = HiringRequest.objects.all()

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return HiringRequestUpdateSerializer
        return HiringRequestSerializer

    def get_queryset(self):
        cid = _company_id(self.request)
        if cid:
            filters = {}
            params = self.request.query_params
            if params.get("department"):
                filters["department"] = params["department"]
            if params.get("status"):
                filters["status"] = params["status"]
            if params.get("job_title"):
                filters["job_title"] = params["job_title"]
            if params.get("created_by"):
                filters["created_by"] = params["created_by"]
            return get_hiring_requests_for_company(cid, filters=filters if filters else None)
        return (
            super().get_queryset()
            .select_related("job_title", "department", "created_by")
            .prefetch_related("approvals")
        )

    # ── Create ──────────────────────────────────────────────────────────────────

    def perform_create(self, serializer):
        serializer.instance = HiringRequestService.create_hiring_request(
            user=self.request.user,
            company=serializer.validated_data["company"],
            data=serializer.validated_data,
        )

    # ── Update (PUT / PATCH) ────────────────────────────────────────────────────

    def perform_update(self, serializer):
        """Route updates through the service to enforce state guards + audit log."""
        try:
            serializer.instance = HiringRequestService.update_hiring_request(
                request_id=self.get_object().pk,
                user=self.request.user,
                data=serializer.validated_data,
            )
        except ValueError as e:
            raise serializer.ValidationError({"detail": str(e)})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.instance = HiringRequestService.update_hiring_request(
                request_id=instance.pk,
                user=request.user,
                data=serializer.validated_data,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        # Return full representation using the read serializer
        return Response(HiringRequestSerializer(serializer.instance).data)

    # ── Delete ──────────────────────────────────────────────────────────────────

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            HiringRequestService.soft_delete_hiring_request(
                request_id=instance.pk,
                user=request.user,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Workflow actions ─────────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        """Submit a draft request for approval."""
        try:
            obj = HiringRequestService.submit_hiring_request(pk, request.user)
            return Response(HiringRequestSerializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """Approve one step in the approval chain."""
        role_type = request.data.get("role_type")
        if not role_type:
            return Response({"detail": "role_type is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            obj = HiringRequestService.approve_request(
                int(pk), request.user, role_type, request.data.get("note", "")
            )
            return Response(HiringRequestSerializer(obj).data)
        except (ValueError, HiringRequestApproval.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        """Reject the request at any approval step."""
        role_type = request.data.get("role_type")
        reason = request.data.get("reason")
        if not role_type or not reason:
            return Response(
                {"detail": "role_type and reason are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            obj = HiringRequestService.reject_request(pk, request.user, role_type, reason)
            return Response(HiringRequestSerializer(obj).data)
        except (ValueError, HiringRequestApproval.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """
        Cancel a draft or submitted request.

        Body (optional):
          { "reason": "string" }
        """
        try:
            obj = HiringRequestService.cancel_hiring_request(
                request_id=int(pk),
                user=request.user,
                reason=request.data.get("reason", ""),
            )
            return Response(HiringRequestSerializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], url_path="approval-flow")
    def approval_flow(self, request, pk=None):
        """Return the full approval chain timeline for a hiring request."""
        instance = self.get_object()
        approvals = instance.approvals.order_by("created_at")
        from .serializers import ApprovalFlowSerializer
        return Response(ApprovalFlowSerializer(approvals, many=True).data)

    @action(detail=False, methods=["post"], url_path="bulk-approve")
    def bulk_approve(self, request):
        """Bulk approve hiring requests."""
        ids = request.data.get("ids", [])
        role_type = request.data.get("role_type")
        note = request.data.get("note", "")
        if not role_type:
            return Response({"detail": "role_type is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from ...application.services.bulk_action_service import BulkActionService
            result = BulkActionService.bulk_approve_hiring_requests(ids, request.user, role_type, note)
            return Response(result)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="bulk-reject")
    def bulk_reject(self, request):
        """Bulk reject hiring requests."""
        ids = request.data.get("ids", [])
        role_type = request.data.get("role_type")
        reason = request.data.get("reason", "")
        if not role_type or not reason:
            return Response({"detail": "role_type and reason are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from ...application.services.bulk_action_service import BulkActionService
            result = BulkActionService.bulk_reject_hiring_requests(ids, request.user, role_type, reason)
            return Response(result)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request):
        """Bulk delete (soft) hiring requests."""
        ids = request.data.get("ids", [])
        try:
            from ...application.services.bulk_action_service import BulkActionService
            result = BulkActionService.bulk_delete_hiring_requests(ids, request.user)
            return Response(result)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ─── Job Advertisement ─────────────────────────────────────────────────────────

class JobAdvertisementViewSet(viewsets.ModelViewSet):
    """
    CRUD + workflow actions for Job Advertisements.

    Lifecycle:
      draft → [publish] → published → [close] → closed → [reopen] → draft

    Edit rules (enforced by service):
      - PUT/PATCH on DRAFT:     all content fields editable.
      - PUT/PATCH on PUBLISHED: only deadline and platforms editable.
      - PUT/PATCH on CLOSED:    not allowed.
      - DELETE:                 only DRAFT ads can be deleted (soft delete).
    """
    queryset = JobAdvertisement.objects.all()

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return JobAdvertisementUpdateSerializer
        return JobAdvertisementSerializer

    def get_queryset(self):
        cid = _company_id(self.request)
        params = self.request.query_params
        if cid:
            filters = {}
            for key in ("status", "city", "area", "platforms", "deadline_before", "deadline_after"):
                if params.get(key):
                    filters[key] = params[key]
            return get_advertisements_for_company(cid, filters=filters if filters else None)
        return (
            super().get_queryset()
            .select_related("hiring_request__job_title", "hiring_request__department")
        )

    # ── Update (PUT / PATCH) ────────────────────────────────────────────────────

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            updated = JobAdvertisementService.update_advertisement(
                ad_id=instance.pk,
                user=request.user,
                data=serializer.validated_data,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(JobAdvertisementSerializer(updated).data)

    # ── Delete ──────────────────────────────────────────────────────────────────

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            JobAdvertisementService.soft_delete_advertisement(
                ad_id=instance.pk,
                user=request.user,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Workflow actions ─────────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        """
        Publish a draft advertisement.

        Body (optional):
          { "deadline": "YYYY-MM-DD", "platforms": ["internal", "linkedin"] }
        """
        try:
            obj = JobAdvertisementService.publish_advertisement(pk, request.user, request.data)
            return Response(JobAdvertisementSerializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        """Close a published advertisement."""
        try:
            obj = JobAdvertisementService.close_advertisement(pk, request.user)
            return Response(JobAdvertisementSerializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="reopen")
    def reopen(self, request, pk=None):
        """
        Reopen a closed advertisement back to draft for revision.
        Clears closed_at so it can be re-published cleanly.
        """
        try:
            obj = JobAdvertisementService.reopen_advertisement(pk, request.user)
            return Response(JobAdvertisementSerializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="bulk-publish")
    def bulk_publish(self, request):
        """Bulk publish job advertisements."""
        ids = request.data.get("ids", [])
        try:
            from ...application.services.bulk_action_service import BulkActionService
            result = BulkActionService.bulk_publish_advertisements(ids, request.user)
            return Response(result)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="bulk-close")
    def bulk_close(self, request):
        """Bulk close job advertisements."""
        ids = request.data.get("ids", [])
        try:
            from ...application.services.bulk_action_service import BulkActionService
            result = BulkActionService.bulk_close_advertisements(ids, request.user)
            return Response(result)
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
        params = self.request.query_params
        if cid:
            filters = {}
            for key in ("status", "classification", "job_board", "job_advertisement", "candidate"):
                if params.get(key):
                    filters[key] = params[key]
            return get_applications_for_company(cid, filters=filters if filters else None)
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

    @action(detail=False, methods=["post"], url_path="import-cvs")
    def import_cvs(self, request):
        """Import candidates from Excel/CSV file."""
        from rest_framework.parsers import MultiPartParser
        file = request.FILES.get("file")
        job_ad_id = request.data.get("job_advertisement_id")
        if not file:
            return Response({"detail": "file is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not job_ad_id:
            return Response({"detail": "job_advertisement_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from ...application.services.import_service import ImportService
            from .serializers import ImportSummarySerializer
            result = ImportService.import_cvs(file, int(job_ad_id), _company_id(request), request.user)
            return Response(ImportSummarySerializer(result).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="sync-from-job-boards")
    def sync_from_job_boards(self, request):
        """Sync candidates from external job boards (placeholder)."""
        job_ad_id = request.data.get("job_advertisement_id")
        platforms = request.data.get("platforms", [])
        if not job_ad_id:
            return Response({"detail": "job_advertisement_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from ...application.services.job_board_sync_service import JobBoardSyncService
            from .serializers import SyncResultSerializer
            result = JobBoardSyncService.sync(int(job_ad_id), platforms, _company_id(request))
            return Response(SyncResultSerializer(result).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="bulk-edit")
    def bulk_edit(self, request):
        """Bulk update classification on multiple applications."""
        ids = request.data.get("ids", [])
        classification = request.data.get("classification")
        if not classification:
            return Response({"detail": "classification is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from ...application.services.bulk_action_service import BulkActionService
            result = BulkActionService.bulk_edit_applications(ids, request.user, classification)
            return Response(result)
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
        qs = (
            super().get_queryset()
            .select_related("application", "application__candidate")
            .prefetch_related("interviewers")
        )
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
                pk, request.user, scoring,
                note=request.data.get("note"),
                call_status=request.data.get("call_status"),
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


# ─── Recruitment Audit Log ─────────────────────────────────────────────────────

from rest_framework.pagination import PageNumberPagination
from apps.audit.models import ActivityLog


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class RecruitmentAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only audit log scoped to recruitment entity types."""
    pagination_class = StandardResultsSetPagination

    ENTITY_TYPE_MAP = {
        "hiring-requests":    "hiring_request",
        "job-advertisements": "job_advertisement",
        "applications":       "application",
    }

    def get_serializer_class(self):
        from .serializers import ActivityLogSerializer
        return ActivityLogSerializer

    def get_queryset(self):
        entity_key = self.kwargs.get("entity_type", "")
        entity_type = self.ENTITY_TYPE_MAP.get(entity_key)
        if not entity_type:
            return ActivityLog.objects.none()

        cid = _company_id(self.request)
        qs = ActivityLog.objects.filter(
            company_id=cid,
            entity_type=entity_type,
        ).select_related("user").order_by("-created_at")

        # Apply filters
        params = self.request.query_params
        if params.get("action_type"):
            qs = qs.filter(action=params["action_type"])
        if params.get("performed_by"):
            qs = qs.filter(user_id=params["performed_by"])
        if params.get("from_date"):
            qs = qs.filter(created_at__date__gte=params["from_date"])
        if params.get("to_date"):
            qs = qs.filter(created_at__date__lte=params["to_date"])
        if params.get("search"):
            qs = qs.filter(action__icontains=params["search"])

        return qs


# ─── Post-Probation Evaluation ─────────────────────────────────────────────────

class PostProbationEvaluationViewSet(viewsets.ModelViewSet):
    """CRUD + workflow actions for Post-Probation Evaluations."""

    def get_serializer_class(self):
        from .serializers import PostProbationEvaluationSerializer
        return PostProbationEvaluationSerializer

    def get_queryset(self):
        from ...models import PostProbationEvaluation
        cid = _company_id(self.request)
        qs = PostProbationEvaluation.objects.select_related(
            "application__candidate", "evaluated_by"
        )
        if cid:
            qs = qs.filter(application__candidate__company_id=cid)
        return qs

    @action(detail=True, methods=["post"], url_path="submit-to-manager")
    def submit_to_manager(self, request, pk=None):
        try:
            from ...application.services.post_probation_service import PostProbationService
            from .serializers import PostProbationEvaluationSerializer
            obj = PostProbationService.submit_to_manager(pk, request.user)
            return Response(PostProbationEvaluationSerializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="manager-approve")
    def manager_approve(self, request, pk=None):
        try:
            from ...application.services.post_probation_service import PostProbationService
            from .serializers import PostProbationEvaluationSerializer
            obj = PostProbationService.manager_approve(pk, request.user, request.data.get("note", ""))
            return Response(PostProbationEvaluationSerializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="hr-confirm")
    def hr_confirm(self, request, pk=None):
        try:
            from ...application.services.post_probation_service import PostProbationService
            from .serializers import PostProbationEvaluationSerializer
            obj = PostProbationService.hr_confirm(pk, request.user, request.data.get("note", ""))
            return Response(PostProbationEvaluationSerializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="record-decision")
    def record_decision(self, request, pk=None):
        decision = request.data.get("decision")
        if not decision:
            return Response({"detail": "decision is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from ...application.services.post_probation_service import PostProbationService
            from .serializers import PostProbationEvaluationSerializer
            obj = PostProbationService.record_decision(
                pk, request.user, decision, request.data.get("rationale", "")
            )
            return Response(PostProbationEvaluationSerializer(obj).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
