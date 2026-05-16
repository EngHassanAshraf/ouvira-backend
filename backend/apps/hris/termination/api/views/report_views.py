"""
Report Views / Hisobot Ko'rinishlari

API endpoints for termination analytics and reports
Tugatish tahlillari va hisobotlari uchun API endpointlari
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.hris.termination.selectors import TerminationSelector


class TerminationStatisticsView(APIView):
    """
    Get termination statistics for company
    Kompaniya uchun tugatish statistikasini olish

    GET: Get statistics with optional date filters
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get termination statistics / Tugatish statistikasini olish"""
        company = request.user.employee.company

        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        statistics = TerminationSelector.get_termination_statistics(
            company=company,
            start_date=start_date,
            end_date=end_date
        )

        return Response({
            'message': 'Termination statistics retrieved',
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'data': statistics
        })


class ExitInterviewInsightsView(APIView):
    """
    Get insights from exit interviews
    Chiqish suhbatlaridan tushunchalar olish

    GET: Get insights with optional date filters
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get exit interview insights / Chiqish suhbati tushunchalarini olish"""
        company = request.user.employee.company

        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        insights = TerminationSelector.get_exit_interview_insights(
            company=company,
            start_date=start_date,
            end_date=end_date
        )

        return Response({
            'message': 'Exit interview insights retrieved',
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'data': insights
        })


class SettlementSummaryView(APIView):
    """
    Get settlement summary for company
    Kompaniya uchun hisob-kitob xulosasini olish

    GET: Get summary with optional date filters
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get settlement summary / Hisob-kitob xulosasini olish"""
        company = request.user.employee.company

        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        summary = TerminationSelector.get_settlement_summary(
            company=company,
            start_date=start_date,
            end_date=end_date
        )

        return Response({
            'message': 'Settlement summary retrieved',
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'data': summary
        })


class PendingApprovalsView(APIView):
    """
    Get all pending approvals for manager/GM
    Menejer/GM uchun barcha kutilayotgan tasdiqlashlarni olish

    GET: Get pending resignations and terminations
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get pending approvals / Kutilayotgan tasdiqlashlarni olish"""
        manager = request.user.employee
        company = manager.company

        # Get pending for manager
        pending_manager = TerminationSelector.get_pending_resignations_for_manager(
            manager=manager,
            company=company
        )

        # Get pending for GM
        pending_gm = TerminationSelector.get_pending_resignations_for_gm(
            company=company
        )

        from apps.hris.termination.serializers import TerminationRequestListSerializer

        return Response({
            'message': 'Pending approvals retrieved',
            'data': {
                'pending_manager_approval': {
                    'count': pending_manager.count(),
                    'items': TerminationRequestListSerializer(pending_manager, many=True).data
                },
                'pending_gm_approval': {
                    'count': pending_gm.count(),
                    'items': TerminationRequestListSerializer(pending_gm, many=True).data
                }
            }
        })