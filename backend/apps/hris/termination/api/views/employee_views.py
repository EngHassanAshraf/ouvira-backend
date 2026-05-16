"""
Employee Views / Xodim Ko'rinishlari

API endpoints for employees to manage their own termination data
Xodimlar o'z tugatish ma'lumotlarini boshqarish uchun API endpointlari
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.hris.termination.models import TerminationRequest, TerminationWarning
from apps.hris.termination.services import ResignationService
from apps.hris.termination.selectors import TerminationSelector
from apps.hris.termination.serializers import (
    TerminationRequestListSerializer,
    TerminationRequestDetailSerializer,
    ResignationCreateSerializer,
    ResignationWithdrawSerializer,
    TerminationWarningListSerializer,
)


class MyResignationView(APIView):
    """
    Employee can view and submit their resignation
    Xodim o'z iste'fosini ko'rishi va yuborishi mumkin

    GET: View my active resignation
    POST: Submit new resignation
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get my active resignation / Mening faol iste'fomni olish"""
        employee = request.user.employee

        # Get active resignation
        resignation = TerminationSelector.get_active_resignation(employee)

        if not resignation:
            return Response({
                'message': 'No active resignation found',
                'data': None
            })

        serializer = TerminationRequestDetailSerializer(resignation)
        return Response({
            'message': 'Active resignation retrieved',
            'data': serializer.data
        })

    def post(self, request):
        """Submit resignation / Iste'fo yuborish"""
        employee = request.user.employee

        # Validate input
        serializer = ResignationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Submit resignation
        resignation = ResignationService.submit_resignation(
            employee=employee,
            reason=serializer.validated_data['reason'],
            notice_period_days=serializer.validated_data.get('notice_period_days', 30),
            attachment=serializer.validated_data.get('attachment'),
            requested_by=employee
        )

        response_serializer = TerminationRequestDetailSerializer(resignation)
        return Response({
            'message': 'Resignation submitted successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class MyResignationWithdrawView(APIView):
    """
    Employee can withdraw their resignation (within 7 days)
    Xodim iste'fosini qaytarib olishi mumkin (7 kun ichida)

    POST: Withdraw resignation
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, resignation_id):
        """Withdraw resignation / Iste'foni qaytarib olish"""
        employee = request.user.employee

        # Get resignation
        try:
            resignation = TerminationRequest.objects.get(
                id=resignation_id,
                employee=employee,
                is_deleted=False
            )
        except TerminationRequest.DoesNotExist:
            return Response({
                'error': 'Resignation not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate input
        serializer = ResignationWithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Withdraw resignation
        resignation = ResignationService.withdraw_resignation(
            resignation=resignation,
            employee=employee,
            withdrawal_reason=serializer.validated_data['withdrawal_reason']
        )

        response_serializer = TerminationRequestDetailSerializer(resignation)
        return Response({
            'message': 'Resignation withdrawn successfully',
            'data': response_serializer.data
        })


class MyTerminationHistoryView(APIView):
    """
    Employee can view their termination history
    Xodim o'z tugatish tarixini ko'rishi mumkin

    GET: List all my termination requests
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get my termination history / Mening tugatish tarixim"""
        employee = request.user.employee

        terminations = TerminationSelector.get_employee_termination_requests(
            employee=employee,
            include_deleted=False
        )

        serializer = TerminationRequestListSerializer(terminations, many=True)
        return Response({
            'message': 'Termination history retrieved',
            'count': terminations.count(),
            'data': serializer.data
        })


class MyTerminationDetailView(APIView):
    """
    Employee can view their termination details
    Xodim o'z tugatish tafsilotlarini ko'rishi mumkin

    GET: View termination details
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, termination_id):
        """Get termination details / Tugatish tafsilotlarini olish"""
        employee = request.user.employee

        # Get termination
        try:
            termination = TerminationRequest.objects.get(
                id=termination_id,
                employee=employee,
                is_deleted=False
            )
        except TerminationRequest.DoesNotExist:
            return Response({
                'error': 'Termination not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get full details
        termination = TerminationSelector.get_termination_detail(termination_id)

        serializer = TerminationRequestDetailSerializer(termination)
        return Response({
            'message': 'Termination details retrieved',
            'data': serializer.data
        })


class MyWarningsView(APIView):
    """
    Employee can view their warnings
    Xodim o'z ogohlantirishlarini ko'rishi mumkin

    GET: List my warnings
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get my warnings / Mening ogohlantirishlarim"""
        employee = request.user.employee

        # Get query parameters
        warning_type = request.query_params.get('warning_type')
        warning_status = request.query_params.get('status')

        warnings = TerminationSelector.get_employee_warnings(
            employee=employee,
            warning_type=warning_type,
            status=warning_status
        )

        serializer = TerminationWarningListSerializer(warnings, many=True)
        return Response({
            'message': 'Warnings retrieved',
            'count': warnings.count(),
            'data': serializer.data
        })