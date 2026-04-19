from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.access_control.permissions.IsAdminUser import IsAdminUser
from apps.hris.leave_management.api.serializers import (
    LeaveRequestListSerializer,
    LeaveRequestDetailSerializer,
    DeclineSerializer,
    InterruptSerializer,
    BulkActionSerializer,
)
from apps.hris.leave_management.services import (
    LeaveApprovalService,
)
from apps.hris.leave_management.selectors.selectors import LeaveSelector


class ManagerLeaveRequestListView(APIView):
    """
    GET — kompaniyadagi barcha so'rovlar (filter + sort)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        company_id = request.tenant.id

        leave_requests = LeaveSelector.get_company_requests(
            company_id=company_id,
            status=request.query_params.get("status"),
            leave_type_id=request.query_params.get("leave_type_id"),
            department_id=request.query_params.get("department_id"),
            start_date=request.query_params.get("start_date"),
            end_date=request.query_params.get("end_date"),
            ordering=request.query_params.get("ordering", "-created_at"),
        )
        serializer = LeaveRequestListSerializer(leave_requests, many=True)
        return Response(serializer.data)


class ManagerApproveView(APIView):
    """
    POST — 1-bosqich: Direct Manager tasdiqlaydi
    PENDING → MANAGER_APPROVED
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        manager_id = request.user.employee_id
        try:
            leave_request = LeaveApprovalService.manager_approve(
                leave_request_id=pk,
                manager_id=manager_id,
            )
            return Response(LeaveRequestDetailSerializer(leave_request).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HRApproveView(APIView):
    """
    POST — 2-bosqich: HR Director tasdiqlaydi
    MANAGER_APPROVED → APPROVED
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        hr_id = request.user.employee_id
        try:
            leave_request = LeaveApprovalService.hr_approve(
                leave_request_id=pk,
                hr_id=hr_id,
            )
            return Response(LeaveRequestDetailSerializer(leave_request).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeclineView(APIView):
    """
    POST — Rad etish (istalgan bosqichda, reason majburiy)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        serializer = DeclineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        declined_by_id = request.user.employee_id
        try:
            leave_request = LeaveApprovalService.decline(
                leave_request_id=pk,
                declined_by_id=declined_by_id,
                reason=serializer.validated_data["reason"],
            )
            return Response(LeaveRequestDetailSerializer(leave_request).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InterruptView(APIView):
    """
    POST — Ta'tildagi xodimni to'xtatish
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        serializer = InterruptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interrupted_by_id = request.user.employee_id
        try:
            leave_request = LeaveApprovalService.interrupt(
                leave_request_id=pk,
                interrupted_by_id=interrupted_by_id,
                interruption_date=serializer.validated_data["interruption_date"],
            )
            return Response(LeaveRequestDetailSerializer(leave_request).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BulkApproveView(APIView):
    """
    POST — Bir vaqtda ko'p so'rovlarni tasdiqlash
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = BulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_by_id = request.user.employee_id
        step = request.query_params.get("step", "manager")

        results = LeaveApprovalService.bulk_approve(
            leave_request_ids=serializer.validated_data["leave_request_ids"],
            approved_by_id=approved_by_id,
            step=step,
        )
        return Response(results)


class BulkDeclineView(APIView):
    """
    POST — Bir vaqtda ko'p so'rovlarni rad etish
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = BulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        declined_by_id = request.user.employee_id
        reason = serializer.validated_data.get("reason", "")

        results = LeaveApprovalService.bulk_decline(
            leave_request_ids=serializer.validated_data["leave_request_ids"],
            declined_by_id=declined_by_id,
            reason=reason,
        )
        return Response(results)