from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from apps.hris.leave_management.api.serializers import (
    LeaveRequestCreateSerializer,
    LeaveRequestListSerializer,
    LeaveRequestDetailSerializer,
)
from apps.hris.leave_management.services import (
    LeaveRequestService,
)
from apps.hris.leave_management.selectors.selectors import LeaveSelector


class LeaveRequestListCreateView(APIView):
    """
    GET  — retrieve all employee requests (with filtering and sorting)
       (filter + sort), retrieve all employee requests (with filtering and sorting), — xodimning barcha so'rovlari

    POST — create a new request , yangi so'rov yaratish
            create a nwe request
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee_id = request.user.employee_id

        leave_requests = LeaveSelector.get_employee_requests(
            employee_id=employee_id,
            status=request.query_params.get("status"),
            leave_type_ids=request.query_params.get("leave_type_id"),
            start_date=request.query_params.get("start_date"),
            end_date=request.query_params.get("end_date"),
            duration_min=request.query_params.get("duration_min"),
            duration_max=request.query_params.get("duration_max"),
            ordering=request.query_params.get("ordering", "-created_at"),
        )
        serializer = LeaveRequestListSerializer(leave_requests, many=True)
        return Response(serializer.data)

    def post(self, request):
        employee_id = request.user.employee_id
        serializer = LeaveRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            leave_request = LeaveRequestService.create_leave_request(
                employee_id=employee_id,
                **serializer.validated_data,
            )
            return Response(
                LeaveRequestDetailSerializer(leave_request).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LeaveRequestDetailView(APIView):
    """
    GET   — retrieve a single request detail, bitta so'rov detail
    PATCH — tahrirlash (faqat Pending), retrieve a single request detail
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee_id = request.user.employee_id
        try:
            leave_request = LeaveSelector.get_request_detail(
                leave_request_id=pk,
                employee_id=employee_id,
            )
            return Response(LeaveRequestDetailSerializer(leave_request).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        employee_id = request.user.employee_id
        serializer = LeaveRequestCreateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            leave_request = LeaveRequestService.update_leave_request(
                leave_request_id=pk,
                employee_id=employee_id,
                **serializer.validated_data,
            )
            return Response(LeaveRequestDetailSerializer(leave_request).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LeaveCancelView(APIView):
    """
    POST — so'rovni bekor qilish (faqat start_date dan oldin)
    - POST — cancel the request (only before the start_date)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        employee_id = request.user.employee_id
        try:
            leave_request = LeaveRequestService.cancel_leave_request(
                leave_request_id=pk,
                employee_id=employee_id,
            )
            return Response(LeaveRequestDetailSerializer(leave_request).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LeaveBalanceSummaryView(APIView):
    """
    GET — xodimning leave balansi (barcha turlar bo'yicha)
    GET — retrieve the employee's leave balance (for all types)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee_id = request.user.employee_id
        year = request.query_params.get("year", timezone.now().year)

        balances = LeaveSelector.get_balance_summary(
            employee_id=employee_id,
            year=int(year),
        )
        from apps.hris.leave_management.api.serializers import LeaveBalanceSerializer
        serializer = LeaveBalanceSerializer(balances, many=True)
        return Response(serializer.data)