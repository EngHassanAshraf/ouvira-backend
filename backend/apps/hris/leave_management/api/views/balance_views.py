from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from apps.access_control.permissions.IsAdminUser import IsAdminUser
from apps.hris.leave_management.api.serializers import (
    LeaveBalanceSerializer,
    LeaveBalanceAdjustSerializer,
)
from apps.hris.leave_management.services import LeaveBalanceService
from apps.hris.leave_management.selectors.selectors import LeaveSelector



class EmployeeBalanceSummaryView(APIView):
    """
    Xodimning barcha ta'til turlari bo'yicha balansi
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee_id = request.user.employee_id
        year = request.query_params.get("year", timezone.now().year)

        balances = LeaveSelector.get_balance_summary(
            employee_id=employee_id,
            year=int(year),
        )
        serializer = LeaveBalanceSerializer(balances, many=True)
        return Response(serializer.data)


class ManagerBalanceSummaryView(APIView):
    """
    Menejer — kompaniyadagi barcha xodimlarning balansi
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, employee_pk):
        year = request.query_params.get("year", timezone.now().year)

        balances = LeaveSelector.get_balance_summary(
            employee_id=employee_pk,
            year=int(year),
        )
        serializer = LeaveBalanceSerializer(balances, many=True)
        return Response(serializer.data)


class BalanceAdjustView(APIView):
    """
    Menejer — xodim balansini qo'lda o'zgartirish (+/-)
    Justification majburiy
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, employee_pk):
        serializer = LeaveBalanceAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        adjusted_by_id = request.user.employee_id

        try:
            balance = LeaveBalanceService.adjust_balance(
                employee_id=employee_pk,
                leave_type_id=serializer.validated_data["leave_type_id"],
                year=serializer.validated_data["year"],
                days=serializer.validated_data["days"],
                adjusted_by_id=adjusted_by_id,
                justification=serializer.validated_data["justification"],
            )
            return Response(LeaveBalanceSerializer(balance).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BalanceInitializeView(APIView):
    """
    Xodim uchun yangi yillik balans yaratish
    Yil boshida yoki yangi xodim qo'shilganda ishlatiladi
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, employee_pk):
        serializer = LeaveBalanceAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            balance = LeaveBalanceService.initialize_balance(
                employee_id=employee_pk,
                leave_type_id=serializer.validated_data["leave_type_id"],
                year=serializer.validated_data["year"],
                total_days=serializer.validated_data["days"],
            )
            return Response(
                LeaveBalanceSerializer(balance).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)