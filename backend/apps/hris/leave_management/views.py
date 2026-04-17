from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from apps.access_control.permissions.IsAdminUser import IsAdminUser
from apps.access_control.permissions.HasModulePermission import make_permission
from apps.hris.leave_management.models import LeaveType, LeaveRequest
from apps.hris.leave_management.serializers import (
    LeaveTypeSerializer,
    LeaveRequestSerializer,
    LeaveRequestCreateSerializer,
    LeaveRequestUpdateSerializer,
)
from apps.hris.leave_management.services import LeaveTypeService, LeaveRequestService
from apps.hris.leave_management.selectors import LeaveTypeSelector, LeaveRequestSelector

# Granular permission classes for leave actions
_CanApproveleave  = make_permission("leave.approve_request")
_CanRejectLeave   = make_permission("leave.reject_request")
_CanManageTypes   = make_permission("leave.manage_types")
_CanEditBalance   = make_permission("leave.edit_balance")


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


# ── Leave Types ────────────────────────────────────────────────────────────────

class LeaveTypeListCreateApiView(APIView):
    """
    GET  /leave-types/  — list all leave types
    POST /leave-types/  — create a leave type (requires leave.manage_types)
    """
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), _CanManageTypes()]

    def get(self, request):
        leave_types = LeaveTypeSelector.get_all_active()
        return Response(LeaveTypeSerializer(leave_types, many=True).data)

    def post(self, request):
        serializer = LeaveTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            leave_type = LeaveTypeService.create_leave_type(**serializer.validated_data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(LeaveTypeSerializer(leave_type).data, status=status.HTTP_201_CREATED)


class LeaveTypeDetailApiView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), _CanManageTypes()]

    def get(self, request, pk):
        lt = get_object_or_404(LeaveType, pk=pk, is_deleted=False)
        return Response(LeaveTypeSerializer(lt).data)

    def patch(self, request, pk):
        serializer = LeaveTypeSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            lt = LeaveTypeService.update_leave_type(pk, **serializer.validated_data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(LeaveTypeSerializer(lt).data)

    def delete(self, request, pk):
        try:
            LeaveTypeService.delete_leave_type(pk)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Leave Requests ─────────────────────────────────────────────────────────────

class LeaveRequestListCreateApiView(ListAPIView):
    """
    GET  /leave-requests/  — paginated, filterable list
    POST /leave-requests/  — submit a new leave request

    Filters  : ?employee=<pk> &status=pending|approved|rejected &leave_type=<pk>
    Ordering : ?ordering=-created_at|start_date|end_date
    """
    serializer_class = LeaveRequestSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "employee": ["exact"],
        "status":   ["exact"],
        "leave_type": ["exact"],
    }
    search_fields = ["employee__first_name", "employee__last_name", "employee__employee_id"]
    ordering_fields = ["created_at", "start_date", "end_date", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = LeaveRequestSelector.get_all()
        employee_id = self.request.query_params.get("employee")
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        req_status = self.request.query_params.get("status")
        if req_status:
            qs = qs.filter(status=req_status)
        leave_type = self.request.query_params.get("leave_type")
        if leave_type:
            qs = qs.filter(leave_type_id=leave_type)
        return qs

    def post(self, request, *args, **kwargs):
        serializer = LeaveRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee_id = request.data.get("employee")
        if not employee_id:
            return Response(
                {"detail": "employee field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            req = LeaveRequestService.create_request(
                employee_id=employee_id, **serializer.validated_data
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(LeaveRequestSerializer(req).data, status=status.HTTP_201_CREATED)


class LeaveRequestDetailApiView(APIView):
    """
    GET    /leave-requests/<pk>/         — retrieve
    PATCH  /leave-requests/<pk>/         — edit (only pending, only owner)
    DELETE /leave-requests/<pk>/cancel/  — cancel
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        req = get_object_or_404(LeaveRequest, pk=pk, is_deleted=False)
        return Response(LeaveRequestSerializer(req).data)

    def patch(self, request, pk):
        serializer = LeaveRequestUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        employee_id = request.data.get("employee")
        if not employee_id:
            return Response(
                {"detail": "employee field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            req = LeaveRequestService.update_request(
                request_id=pk,
                employee_id=employee_id,
                **serializer.validated_data,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(LeaveRequestSerializer(req).data)


class LeaveRequestCancelApiView(APIView):
    """DELETE /leave-requests/<pk>/cancel/ — cancel a request"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        employee_id = request.data.get("employee")
        if not employee_id:
            return Response(
                {"detail": "employee field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            LeaveRequestService.cancel_request(
                request_id=pk, employee_id=employee_id
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LeaveRequestApproveApiView(APIView):
    """POST /leave-requests/<pk>/approve/"""
    permission_classes = [IsAuthenticated, _CanApproveleave]

    def post(self, request, pk):
        approver_employee_id = request.data.get("approver_employee_id")
        if not approver_employee_id:
            return Response(
                {"detail": "approver_employee_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            req = LeaveRequestService.approve_request(
                request_id=pk, approver_employee_id=approver_employee_id
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(LeaveRequestSerializer(req).data)


class LeaveRequestRejectApiView(APIView):
    """POST /leave-requests/<pk>/reject/"""
    permission_classes = [IsAuthenticated, _CanRejectLeave]

    def post(self, request, pk):
        approver_employee_id = request.data.get("approver_employee_id")
        if not approver_employee_id:
            return Response(
                {"detail": "approver_employee_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            req = LeaveRequestService.reject_request(
                request_id=pk, approver_employee_id=approver_employee_id
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(LeaveRequestSerializer(req).data)
