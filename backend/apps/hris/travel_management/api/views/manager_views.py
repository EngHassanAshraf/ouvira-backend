from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.access_control.permissions.HasModulePermission import make_permission
from apps.hris.travel_management.services import (
    BusinessTripRequestService,
    BusinessTripApprovalService,
)
from apps.hris.travel_management.selectors import BusinessTripSelector
from apps.hris.travel_management.serializers import (
    BusinessTripRequestCreateSerializer,
    BusinessTripRequestListSerializer,
    BusinessTripRequestDetailSerializer,
    DeclineSerializer,
    InterruptSerializer,
    BulkActionSerializer,
)


class ManagerBusinessTripRequestListView(APIView):
    """
    GET  — barcha xodimlar so'rovlari (manager uchun)
    POST — on behalf of yaratish
    """
    permission_classes = [IsAuthenticated, make_permission("travel.view_all_requests")]

    def get(self, request):
        company_id = request.tenant.id

        trips = BusinessTripSelector.get_company_requests(
            company_id=company_id,
            status=request.query_params.get("status"),
            employee_id=request.query_params.get("employee_id"),
            department_id=request.query_params.get("department_id"),
            destination=request.query_params.get("destination"),
            start_date=request.query_params.get("start_date"),
            end_date=request.query_params.get("end_date"),
            ordering=request.query_params.get("ordering", "-created_at"),
        )
        serializer = BusinessTripRequestListSerializer(trips, many=True)
        return Response(serializer.data)

    def post(self, request):
        """On behalf of — manager xodim nomidan yaratadi"""
        company_id = request.tenant.id
        created_by_id = request.user.employee.id

        serializer = BusinessTripRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        employee_id = data.pop("employee_id", None)

        if not employee_id:
            return Response(
                {"error": "employee_id is required for on_behalf_of creation"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        trip = BusinessTripRequestService.create_request(
            employee_id=employee_id,
            company_id=company_id,
            created_by_id=created_by_id,
            **data,
        )
        return Response(
            BusinessTripRequestDetailSerializer(trip).data,
            status=status.HTTP_201_CREATED,
        )


class ManagerApproveView(APIView):
    """POST — manager tasdiqlaydi (1-bosqich)"""
    permission_classes = [IsAuthenticated, make_permission("travel.approve_request")]

    def post(self, request, pk):
        manager_id = request.user.employee.id
        company_id = request.tenant.id

        trip = BusinessTripApprovalService.manager_approve(
            trip_request_id=pk,
            manager_id=manager_id,
            company_id=company_id,
        )
        return Response(BusinessTripRequestDetailSerializer(trip).data)


class HRApproveView(APIView):
    """POST — HR tasdiqlaydi (2-bosqich)"""
    permission_classes = [IsAuthenticated, make_permission("travel.hr_approve_request")]

    def post(self, request, pk):
        hr_id = request.user.employee.id
        company_id = request.tenant.id

        trip = BusinessTripApprovalService.hr_approve(
            trip_request_id=pk,
            hr_id=hr_id,
            company_id=company_id,
        )
        return Response(BusinessTripRequestDetailSerializer(trip).data)


class DeclineView(APIView):
    """POST — rad etish (manager yoki HR)"""
    permission_classes = [IsAuthenticated, make_permission("travel.approve_request")]

    def post(self, request, pk):
        declined_by_id = request.user.employee.id
        company_id = request.tenant.id

        serializer = DeclineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        trip = BusinessTripApprovalService.decline(
            trip_request_id=pk,
            declined_by_id=declined_by_id,
            company_id=company_id,
            reason=serializer.validated_data["reason"],
        )
        return Response(BusinessTripRequestDetailSerializer(trip).data)


class InterruptView(APIView):
    """POST — active safarni to'xtatish"""
    permission_classes = [IsAuthenticated, make_permission("travel.interrupt_request")]

    def post(self, request, pk):
        interrupted_by_id = request.user.employee.id
        company_id = request.tenant.id

        serializer = InterruptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        trip = BusinessTripApprovalService.interrupt(
            trip_request_id=pk,
            interrupted_by_id=interrupted_by_id,
            company_id=company_id,
            interruption_date=serializer.validated_data["interruption_date"],
        )
        return Response(BusinessTripRequestDetailSerializer(trip).data)


class BulkApproveView(APIView):
    """POST — bulk tasdiqlash"""
    permission_classes = [IsAuthenticated, make_permission("travel.approve_request")]

    def post(self, request):
        approved_by_id = request.user.employee.id
        company_id = request.tenant.id

        serializer = BulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        step = request.query_params.get("step", "manager")  # manager yoki hr

        results = BusinessTripApprovalService.bulk_approve(
            trip_request_ids=serializer.validated_data["trip_request_ids"],
            approved_by_id=approved_by_id,
            company_id=company_id,
            step=step,
        )
        return Response(results)


class BulkDeclineView(APIView):
    """POST — bulk rad etish"""
    permission_classes = [IsAuthenticated, make_permission("travel.approve_request")]

    def post(self, request):
        declined_by_id = request.user.employee.id
        company_id = request.tenant.id

        serializer = BulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not serializer.validated_data.get("reason"):
            return Response(
                {"error": "reason is required for bulk decline"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = BusinessTripApprovalService.bulk_decline(
            trip_request_ids=serializer.validated_data["trip_request_ids"],
            declined_by_id=declined_by_id,
            company_id=company_id,
            reason=serializer.validated_data["reason"],
        )
        return Response(results)