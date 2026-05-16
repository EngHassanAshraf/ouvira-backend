"""
HR Views / HR Ko'rinishlari

API endpoints for HR to manage all termination processes
HR barcha tugatish jarayonlarini boshqarish uchun API endpointlari
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.hris.termination.models import (
    TerminationRequest,
    TerminationWarning,
    TerminationSettlement,
    ExitInterview
)
from apps.hris.termination.services import (
    ResignationService,
    WarningService,
    TerminationService,
    SettlementService,
    ExitInterviewService
)
from apps.hris.termination.selectors import TerminationSelector
from apps.hris.termination.serializers import *


# ========== TERMINATION MANAGEMENT ==========

class TerminationListView(APIView):
    """
    HR can view all terminations with filters
    HR barcha tugatishlarni filtrlar bilan ko'rishi mumkin

    GET: List all terminations
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all terminations / Barcha tugatishlar"""
        company = request.user.employee.company

        # Get query parameters
        termination_type = request.query_params.get('type')
        termination_status = request.query_params.get('status')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        terminations = TerminationSelector.get_company_termination_requests(
            company=company,
            termination_type=termination_type,
            status=termination_status,
            start_date=start_date,
            end_date=end_date
        )

        serializer = TerminationRequestListSerializer(terminations, many=True)
        return Response({
            'message': 'Terminations retrieved',
            'count': terminations.count(),
            'data': serializer.data
        })


class ResignationApproveManagerView(APIView):
    """
    Manager approves resignation (Step 1)
    Menejer iste'foni tasdiqlaydi (1-qadam)

    POST: Approve resignation
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, resignation_id):
        """Manager approve resignation"""
        manager = request.user.employee

        resignation = get_object_or_404(
            TerminationRequest,
            id=resignation_id,
            is_deleted=False
        )

        serializer = TerminationApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resignation = ResignationService.manager_approve_resignation(
            resignation=resignation,
            manager=manager,
            notes=serializer.validated_data.get('notes')
        )

        response_serializer = TerminationRequestDetailSerializer(resignation)
        return Response({
            'message': 'Resignation approved by manager',
            'data': response_serializer.data
        })


class ResignationApproveGMView(APIView):
    """
    GM approves resignation (Step 2 - Final)
    GM iste'foni tasdiqlaydi (2-qadam - Yakuniy)

    POST: GM approve resignation
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, resignation_id):
        """GM approve resignation"""
        gm = request.user.employee

        resignation = get_object_or_404(
            TerminationRequest,
            id=resignation_id,
            is_deleted=False
        )

        serializer = TerminationApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resignation = ResignationService.gm_approve_resignation(
            resignation=resignation,
            gm=gm,
            notes=serializer.validated_data.get('notes')
        )

        response_serializer = TerminationRequestDetailSerializer(resignation)
        return Response({
            'message': 'Resignation approved by GM',
            'data': response_serializer.data
        })


class ResignationRejectView(APIView):
    """
    Reject resignation
    Iste'foni rad etish

    POST: Reject resignation
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, resignation_id):
        """Reject resignation"""
        rejected_by = request.user.employee

        resignation = get_object_or_404(
            TerminationRequest,
            id=resignation_id,
            is_deleted=False
        )

        serializer = TerminationRejectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resignation = ResignationService.reject_resignation(
            resignation=resignation,
            rejected_by=rejected_by,
            rejection_reason=serializer.validated_data['rejection_reason']
        )

        response_serializer = TerminationRequestDetailSerializer(resignation)
        return Response({
            'message': 'Resignation rejected',
            'data': response_serializer.data
        })


class BehavioralTerminationCreateView(APIView):
    """HR initiates behavioral termination"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        initiated_by = request.user.employee

        serializer = BehavioralTerminationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        termination = TerminationService.initiate_behavioral_termination(
            employee=serializer.validated_data['employee'],
            violation_description=serializer.validated_data['violation_description'],
            initiated_by=initiated_by,
            is_gross_violation=serializer.validated_data.get('is_gross_violation', False),
            attachment=serializer.validated_data.get('attachment')
        )

        response_serializer = TerminationRequestDetailSerializer(termination)
        return Response({
            'message': 'Behavioral termination initiated',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class PerformanceTerminationCreateView(APIView):
    """HR initiates performance termination"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        initiated_by = request.user.employee

        serializer = PerformanceTerminationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        termination = TerminationService.initiate_performance_termination(
            employee=serializer.validated_data['employee'],
            performance_issues=serializer.validated_data['performance_issues'],
            initiated_by=initiated_by,
            evaluation_scores=serializer.validated_data.get('evaluation_scores'),
            attachment=serializer.validated_data.get('attachment')
        )

        response_serializer = TerminationRequestDetailSerializer(termination)
        return Response({
            'message': 'Performance termination initiated',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


# ========== WARNING MANAGEMENT ==========

class WarningListView(APIView):
    """HR views all warnings"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.employee.company
        warning_type = request.query_params.get('type')

        warnings = TerminationSelector.get_active_warnings(
            company=company,
            warning_type=warning_type
        )

        serializer = TerminationWarningListSerializer(warnings, many=True)
        return Response({
            'message': 'Warnings retrieved',
            'count': warnings.count(),
            'data': serializer.data
        })


class AbsenceWarningCreateView(APIView):
    """HR issues absence warning"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        issued_by = request.user.employee

        serializer = AbsenceWarningCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        warning = WarningService.issue_absence_warning(
            employee=serializer.validated_data['employee'],
            warning_type=serializer.validated_data['warning_type'],
            absence_start_date=serializer.validated_data['absence_start_date'],
            absence_days_count=serializer.validated_data['absence_days_count'],
            reason=serializer.validated_data['reason'],
            issued_by=issued_by,
            sent_via_registered_mail=serializer.validated_data.get('sent_via_registered_mail', False),
            registered_mail_tracking=serializer.validated_data.get('registered_mail_tracking'),
            form_s6_attached=serializer.validated_data.get('form_s6_attached', False),
            attachment=serializer.validated_data.get('attachment')
        )

        response_serializer = TerminationWarningDetailSerializer(warning)
        return Response({
            'message': 'Absence warning issued',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class PerformanceWarningCreateView(APIView):
    """HR issues performance warning"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        issued_by = request.user.employee

        serializer = PerformanceWarningCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        warning = WarningService.issue_performance_warning(
            employee=serializer.validated_data['employee'],
            evaluation_score=serializer.validated_data['evaluation_score'],
            evaluation_period=serializer.validated_data['evaluation_period'],
            reason=serializer.validated_data['reason'],
            issued_by=issued_by,
            attachment=serializer.validated_data.get('attachment')
        )

        response_serializer = TerminationWarningDetailSerializer(warning)
        return Response({
            'message': 'Performance warning issued',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class WarningEscalateView(APIView):
    """HR escalates final warning to termination"""
    permission_classes = [IsAuthenticated]

    def post(self, request, warning_id):
        escalated_by = request.user.employee

        warning = get_object_or_404(TerminationWarning, id=warning_id, is_deleted=False)

        serializer = WarningEscalateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        warning, termination = WarningService.escalate_warning_to_termination(
            warning=warning,
            escalated_by=escalated_by,
            termination_reason=serializer.validated_data['termination_reason']
        )

        return Response({
            'message': 'Warning escalated to termination',
            'warning': TerminationWarningDetailSerializer(warning).data,
            'termination': TerminationRequestDetailSerializer(termination).data
        })


# ========== SETTLEMENT MANAGEMENT ==========

class SettlementListView(APIView):
    """HR views all settlements"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.employee.company

        settlements = TerminationSelector.get_pending_settlements(company)

        serializer = TerminationSettlementListSerializer(settlements, many=True)
        return Response({
            'message': 'Settlements retrieved',
            'count': settlements.count(),
            'data': serializer.data
        })


class SettlementCreateView(APIView):
    """HR creates settlement"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        calculated_by = request.user.employee

        serializer = SettlementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        settlement = SettlementService.create_settlement(
            termination_request=serializer.validated_data['termination_request'],
            years_of_service=serializer.validated_data['years_of_service'],
            unused_leave_days=serializer.validated_data['unused_leave_days'],
            pending_salary_days=serializer.validated_data['pending_salary_days'],
            calculated_by=calculated_by,
            **{k: v for k, v in serializer.validated_data.items()
               if k not in ['termination_request', 'years_of_service', 'unused_leave_days', 'pending_salary_days']}
        )

        response_serializer = TerminationSettlementDetailSerializer(settlement)
        return Response({
            'message': 'Settlement created',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class SettlementApproveView(APIView):
    """HR/Manager approves settlement"""
    permission_classes = [IsAuthenticated]

    def post(self, request, settlement_id):
        approved_by = request.user.employee

        settlement = get_object_or_404(TerminationSettlement, id=settlement_id, is_deleted=False)

        settlement = SettlementService.approve_settlement(
            settlement=settlement,
            approved_by=approved_by
        )

        serializer = TerminationSettlementDetailSerializer(settlement)
        return Response({
            'message': 'Settlement approved',
            'data': serializer.data
        })


class SettlementPaymentView(APIView):
    """Finance processes settlement payment"""
    permission_classes = [IsAuthenticated]

    def post(self, request, settlement_id):
        paid_by = request.user.employee

        settlement = get_object_or_404(TerminationSettlement, id=settlement_id, is_deleted=False)

        serializer = SettlementPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        settlement = SettlementService.process_payment(
            settlement=settlement,
            payment_date=serializer.validated_data['payment_date'],
            payment_method=serializer.validated_data['payment_method'],
            payment_reference=serializer.validated_data['payment_reference'],
            paid_by=paid_by,
            paid_to_heir=serializer.validated_data.get('paid_to_heir'),
            heir_relationship=serializer.validated_data.get('heir_relationship'),
            heir_identification=serializer.validated_data.get('heir_identification')
        )

        response_serializer = TerminationSettlementDetailSerializer(settlement)
        return Response({
            'message': 'Payment processed',
            'data': response_serializer.data
        })


# ========== EXIT INTERVIEW MANAGEMENT ==========

class ExitInterviewListView(APIView):
    """HR views all exit interviews"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.employee.company

        interviews = TerminationSelector.get_scheduled_exit_interviews(company)

        serializer = ExitInterviewListSerializer(interviews, many=True)
        return Response({
            'message': 'Exit interviews retrieved',
            'count': interviews.count(),
            'data': serializer.data
        })


class ExitInterviewScheduleView(APIView):
    """HR schedules exit interview"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        scheduled_by = request.user.employee

        serializer = ExitInterviewScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interview = ExitInterviewService.schedule_exit_interview(
            termination_request=serializer.validated_data['termination_request'],
            scheduled_date=serializer.validated_data['scheduled_date'],
            scheduled_by=scheduled_by,
            interview_method=serializer.validated_data.get('interview_method', 'in_person'),
            location=serializer.validated_data.get('location')
        )

        response_serializer = ExitInterviewDetailSerializer(interview)
        return Response({
            'message': 'Exit interview scheduled',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class ExitInterviewConductView(APIView):
    """HR conducts exit interview"""
    permission_classes = [IsAuthenticated]

    def post(self, request, interview_id):
        conducted_by = request.user.employee

        interview = get_object_or_404(ExitInterview, id=interview_id, is_deleted=False)

        serializer = ExitInterviewConductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interview = ExitInterviewService.conduct_exit_interview(
            exit_interview=interview,
            conducted_by=conducted_by,
            **serializer.validated_data
        )

        response_serializer = ExitInterviewDetailSerializer(interview)
        return Response({
            'message': 'Exit interview completed',
            'data': response_serializer.data
        })