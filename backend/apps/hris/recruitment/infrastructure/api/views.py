from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .serializers import (
    HiringRequestSerializer, HiringRequestApprovalSerializer, 
    JobAdvertisementSerializer, CandidateSerializer, 
    JobApplicationSerializer, InterviewSerializer, 
    CandidateDocumentSerializer, JobOfferSerializer, 
    OnboardingSerializer
)
from ...models import (
    HiringRequest, HiringRequestApproval, JobAdvertisement, 
    Candidate, JobApplication, Interview, CandidateDocument,
    JobOffer, Onboarding
)
from ...application.services.hiring_request_service import HiringRequestService
from ...application.services.job_advertisement_service import JobAdvertisementService
from ...application.services.application_service import ApplicationService
from ...application.services.interview_service import InterviewService
from ...application.services.document_service import DocumentService
from ...application.services.job_offer_service import JobOfferService

class HiringRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Hiring Requests."""
    serializer_class = HiringRequestSerializer
    queryset = HiringRequest.objects.all()

    def get_queryset(self):
        company_id = self.request.query_params.get('company') or getattr(self.request.user, 'company_id', None)
        queryset = super().get_queryset()
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        return queryset.select_related('job_title', 'department', 'created_by').prefetch_related('approvals')

    def perform_create(self, serializer):
        company = serializer.validated_data.get('company')
        HiringRequestService.create_hiring_request(
            user=self.request.user,
            company=company,
            data=serializer.validated_data
        )

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        try:
            hiring_request = HiringRequestService.submit_hiring_request(pk, request.user)
            serializer = self.get_serializer(hiring_request)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        role_type = request.data.get('role_type')
        if not role_type: return Response({"detail": "role_type is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            hiring_request = HiringRequestService.approve_request(pk, request.user, role_type, request.data.get('note', ''))
            serializer = self.get_serializer(hiring_request)
            return Response(serializer.data)
        except (ValueError, HiringRequestApproval.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        role_type = request.data.get('role_type')
        reason = request.data.get('reason')
        if not role_type or not reason: return Response({"detail": "role_type and reason are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            hiring_request = HiringRequestService.reject_request(pk, request.user, role_type, reason)
            serializer = self.get_serializer(hiring_request)
            return Response(serializer.data)
        except (ValueError, HiringRequestApproval.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class JobAdvertisementViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Job Advertisements."""
    serializer_class = JobAdvertisementSerializer
    queryset = JobAdvertisement.objects.all()

    def get_queryset(self):
        company_id = self.request.query_params.get('company') or getattr(self.request.user, 'company_id', None)
        queryset = super().get_queryset()
        if company_id:
            queryset = queryset.filter(hiring_request__company_id=company_id)
        return queryset.select_related('hiring_request__job_title', 'hiring_request__department')

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        try:
            ad = JobAdvertisementService.publish_advertisement(pk, request.user, request.data)
            serializer = self.get_serializer(ad)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request, pk=None):
        try:
            ad = JobAdvertisementService.close_advertisement(pk, request.user)
            serializer = self.get_serializer(ad)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CandidateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Candidates."""
    serializer_class = CandidateSerializer
    queryset = Candidate.objects.all()

    def get_queryset(self):
        company_id = self.request.query_params.get('company') or getattr(self.request.user, 'company_id', None)
        queryset = super().get_queryset()
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        return queryset


class JobApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Job Applications."""
    serializer_class = JobApplicationSerializer
    queryset = JobApplication.objects.all()

    def get_queryset(self):
        company_id = self.request.query_params.get('company') or getattr(self.request.user, 'company_id', None)
        queryset = super().get_queryset()
        if company_id:
            queryset = queryset.filter(candidate__company_id=company_id)
        return queryset.select_related('candidate', 'job_advertisement')

    @action(detail=True, methods=['post'], url_path='move-to-stage')
    def move_to_stage(self, request, pk=None):
        try:
            application = ApplicationService.move_to_stage(pk, request.data.get('status'), request.user, request.data.get('classification'))
            serializer = self.get_serializer(application)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InterviewViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Interviews."""
    serializer_class = InterviewSerializer
    queryset = Interview.objects.all()

    def get_queryset(self):
        company_id = self.request.query_params.get('company') or getattr(self.request.user, 'company_id', None)
        queryset = super().get_queryset()
        if company_id:
            queryset = queryset.filter(application__candidate__company_id=company_id)
        return queryset.select_related('application', 'application__candidate').prefetch_related('interviewers')

    def perform_create(self, serializer):
        interviewers = self.request.data.get('interviewers', [])
        return InterviewService.schedule_interview(
            application_id=serializer.validated_data.get('application').id,
            interview_type=serializer.validated_data.get('interview_type'),
            interview_date=serializer.validated_data.get('interview_date'),
            interviewers=[int(i) for i in interviewers] if interviewers else []
        )

    @action(detail=True, methods=['post'], url_path='record-result')
    def record_result(self, request, pk=None):
        try:
            interview = InterviewService.record_interview_result(pk, request.user, request.data.get('scoring_data'), request.data.get('note'))
            serializer = self.get_serializer(interview)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CandidateDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Candidate Documents."""
    serializer_class = CandidateDocumentSerializer
    queryset = CandidateDocument.objects.all()

    def get_queryset(self):
        company_id = self.request.query_params.get('company') or getattr(self.request.user, 'company_id', None)
        queryset = super().get_queryset()
        if company_id:
            queryset = queryset.filter(candidate__company_id=company_id)
        return queryset

    @action(detail=True, methods=['post'], url_path='verify')
    def verify(self, request, pk=None):
        try:
            document = DocumentService.verify_document(pk, request.data.get('status'), request.user, request.data.get('note'))
            serializer = self.get_serializer(document)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class JobOfferViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Job Offers (Final Decision)."""
    serializer_class = JobOfferSerializer
    queryset = JobOffer.objects.all()

    def get_queryset(self):
        company_id = self.request.query_params.get('company') or getattr(self.request.user, 'company_id', None)
        queryset = super().get_queryset()
        if company_id:
            queryset = queryset.filter(application__candidate__company_id=company_id)
        return queryset.select_related('application', 'application__candidate')

    def perform_create(self, serializer):
        return JobOfferService.create_offer(
            application_id=serializer.validated_data.get('application').id,
            offer_data=serializer.validated_data
        )

    @action(detail=True, methods=['post'], url_path='accept')
    def accept(self, request, pk=None):
        """Final Decision: Accept offer and create Employee record."""
        try:
            # employee_data includes: employee_id, national_id, gender, date_of_birth
            offer = JobOfferService.accept_offer(pk, request.user, request.data)
            serializer = self.get_serializer(offer)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='decline')
    def decline(self, request, pk=None):
        try:
            offer = JobOfferService.decline_offer(pk, request.user, request.data.get('reason'))
            serializer = self.get_serializer(offer)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OnboardingViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Onboarding checklists."""
    serializer_class = OnboardingSerializer
    queryset = Onboarding.objects.all()

    def get_queryset(self):
        company_id = self.request.query_params.get('company') or getattr(self.request.user, 'company_id', None)
        queryset = super().get_queryset()
        if company_id:
            queryset = queryset.filter(candidate__company_id=company_id)
        return queryset.select_related('candidate')
