from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

from apps.access_control.permissions.HasModulePermission import make_permission
from apps.hris.leave_management.selectors.selectors import LeaveSelector
from apps.hris.leave_management.api.serializers import LeaveBalanceAdjustmentLogSerializer


class LeaveBalanceAdjustmentLogView(APIView):
    """
    EN: Returns balance adjustment history for a company.
    UZ: Kompaniya bo'yicha balans o'zgartirish tarixini qaytaradi.
    """

    permission_classes = [IsAuthenticated, make_permission("leave.edit_balance")]

    @swagger_auto_schema(
        operation_description="Leave balance adjustment history / Balans o'zgartirish tarixi",
        responses={200: LeaveBalanceAdjustmentLogSerializer(many=True)}
    )
    def get(self, request):
        company_id = request.tenant.id

        adjustment = LeaveSelector.get_balance_adjustments(
            company_id=company_id,
            employee_id=request.query_params.get("employee_id"),
            leave_type_id=request.query_params.get("leave-type_id"),
            year=request.query_params.get("year")
        )

        serializer = LeaveBalanceAdjustmentLogSerializer(adjustment, many=True)
        return Response(serializer.data)


