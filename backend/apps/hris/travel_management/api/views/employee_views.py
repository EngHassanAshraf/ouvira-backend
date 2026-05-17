from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.access_control.permissions.HasModulePermission import make_permission
from apps.hris.travel_management.services import BusinessTripRequestService
from apps.hris.travel_management.selectors import BusinessTripSelector
from apps.hris.travel_management.serializers import (
    BusinessTripRequestCreateSerializer,
    BusinessTripRequestUpdateSerializer,
    BusinessTripRequestListSerializer,
    BusinessTripRequestDetailSerializer,
    BusinessTripBalanceDetailSerializer,
)


class BusinessTripRequestListCreateView(APIView):
    """
    GET  — xodimning o'z so'rovlari
    POST — yangi so'rov yaratish
    """
    permission_classes = [IsAuthenticated, make_permission("travel.create_request")]

    def get(self, request):
        employee_id = request.user.employee.id

        trips = BusinessTripSelector.get_employee_requests(
            employee_id=employee_id,
            status=request.query_params.get("status"),
            destination=request.query_params.get("destination"),
            start_date=request.query_params.get("start_date"),
            end_date=request.query_params.get("end_date"),
            ordering=request.query_params.get("ordering", "-created_at"),
        )
        serializer = BusinessTripRequestListSerializer(trips, many=True)
        return Response(serializer.data)

    def post(self, request):
        company_id = request.tenant.id
        employee_id = request.user.employee.id

        serializer = BusinessTripRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        trip = BusinessTripRequestService.create_request(
            employee_id=employee_id,
            company_id=company_id,
            **serializer.validated_data,
        )
        return Response(
            BusinessTripRequestDetailSerializer(trip).data,
            status=status.HTTP_201_CREATED,
        )


class BusinessTripRequestDetailView(APIView):
    """
    GET   — detail
    PATCH — tahrirlash (faqat PENDING)
    """
    permission_classes = [IsAuthenticated, make_permission("travel.view_own_request")]

    def get(self, request, pk):
        employee_id = request.user.employee.id
        trip = BusinessTripSelector.get_request_detail(
            trip_request_id=pk,
            employee_id=employee_id,
        )
        return Response(BusinessTripRequestDetailSerializer(trip).data)

    def patch(self, request, pk):
        employee_id = request.user.employee.id
        company_id = request.tenant.id

        serializer = BusinessTripRequestUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        trip = BusinessTripRequestService.update_request(
            trip_request_id=pk,
            employee_id=employee_id,
            company_id=company_id,
            **serializer.validated_data,
        )
        return Response(BusinessTripRequestDetailSerializer(trip).data)


class BusinessTripRequestCancelView(APIView):
    """POST — so'rovni bekor qilish"""
    permission_classes = [IsAuthenticated, make_permission("travel.cancel_request")]

    def post(self, request, pk):
        employee_id = request.user.employee.id
        company_id = request.tenant.id

        trip = BusinessTripRequestService.cancel_request(
            trip_request_id=pk,
            employee_id=employee_id,
            company_id=company_id,
        )
        return Response(BusinessTripRequestDetailSerializer(trip).data)


class MyBusinessTripBalanceView(APIView):
    """GET — xodimning o'z balansi"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        employee_id = request.user.employee.id
        year = int(request.query_params.get("year", timezone.now().year))

        balance = BusinessTripSelector.get_employee_balance(
            employee_id=employee_id,
            year=year,
        )
        return Response(BusinessTripBalanceDetailSerializer(balance).data)