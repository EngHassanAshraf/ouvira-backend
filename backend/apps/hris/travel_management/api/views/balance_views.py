from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.http import HttpResponse
from django.utils import timezone

from apps.access_control.permissions.HasModulePermission import make_permission
from apps.hris.travel_management.services import BusinessTripBalanceService
from apps.hris.travel_management.selectors import BusinessTripSelector
from apps.hris.travel_management.serializers import (
    BusinessTripBalanceSerializer,
    BusinessTripBalanceDetailSerializer,
    BusinessTripBalanceAdjustSerializer,
    BusinessTripBulkAdjustSerializer,
    BusinessTripCSVImportSerializer,
    BusinessTripBalanceAdjustmentLogSerializer,
)


class BusinessTripBalanceListView(APIView):
    """GET — barcha xodimlar balansi (HR)"""
    permission_classes = [IsAuthenticated, make_permission("travel.view_balance")]

    def get(self, request):
        company_id = request.tenant.id
        year = int(request.query_params.get("year", timezone.now().year))

        balances = BusinessTripSelector.get_balance_list(
            company_id=company_id,
            year=year,
            employee_id=request.query_params.get("employee_id"),
            department_id=request.query_params.get("department_id"),
            ordering=request.query_params.get("ordering", "-total_days"),
        )
        serializer = BusinessTripBalanceSerializer(balances, many=True)
        return Response(serializer.data)


class BusinessTripBalanceDetailView(APIView):
    """GET — bitta xodim balansi + adjustment history"""
    permission_classes = [IsAuthenticated, make_permission("travel.view_balance")]

    def get(self, request, pk):
        company_id = request.tenant.id
        balance = BusinessTripSelector.get_balance_detail(
            balance_id=pk,
            company_id=company_id,
        )
        serializer = BusinessTripBalanceDetailSerializer(balance)
        return Response(serializer.data)


class BusinessTripBalanceAdjustView(APIView):
    """POST — individual balans o'zgartirish"""
    permission_classes = [IsAuthenticated, make_permission("travel.manage_balance")]

    def post(self, request, pk):
        performed_by_id = request.user.employee.id
        company_id = request.tenant.id

        serializer = BusinessTripBalanceAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        balance = BusinessTripBalanceService.adjust_balance(
            balance_id=pk,
            company_id=company_id,
            performed_by_id=performed_by_id,
            **serializer.validated_data,
        )
        return Response(BusinessTripBalanceDetailSerializer(balance).data)


class BusinessTripBulkAdjustView(APIView):
    """POST — bulk balans o'zgartirish"""
    permission_classes = [IsAuthenticated, make_permission("travel.manage_balance")]

    def post(self, request):
        performed_by_id = request.user.employee.id
        company_id = request.tenant.id

        serializer = BusinessTripBulkAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        results = BusinessTripBalanceService.bulk_adjust(
            company_id=company_id,
            performed_by_id=performed_by_id,
            **serializer.validated_data,
        )
        return Response(results)


class BusinessTripCSVImportView(APIView):
    """POST — CSV import"""
    permission_classes = [IsAuthenticated, make_permission("travel.manage_balance")]

    def post(self, request):
        performed_by_id = request.user.employee.id
        company_id = request.tenant.id

        serializer = BusinessTripCSVImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        results = BusinessTripBalanceService.import_from_csv(
            company_id=company_id,
            performed_by_id=performed_by_id,
            file=serializer.validated_data["file"],
        )
        return Response(results)


class BusinessTripCSVTemplateView(APIView):
    """GET — CSV template yuklab olish"""
    permission_classes = [IsAuthenticated, make_permission("travel.manage_balance")]

    def get(self, request):
        csv_content = BusinessTripBalanceService.get_csv_template()
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="business_trip_balance_template.csv"'
        return response


class BusinessTripAdjustmentLogView(APIView):
    """GET — Active Log (adjustment tarixi)"""
    permission_classes = [IsAuthenticated, make_permission("travel.view_balance")]

    def get(self, request):
        company_id = request.tenant.id

        adjustments = BusinessTripSelector.get_balance_adjustments(
            company_id=company_id,
            employee_id=request.query_params.get("employee_id"),
            year=request.query_params.get("year"),
            adjustment_type=request.query_params.get("adjustment_type"),
            ordering=request.query_params.get("ordering", "-created_at"),
        )
        serializer = BusinessTripBalanceAdjustmentLogSerializer(adjustments, many=True)
        return Response(serializer.data)