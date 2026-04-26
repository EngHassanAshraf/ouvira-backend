import csv
import io


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

from apps.access_control.permissions.HasModulePermission import make_permission
from apps.hris.leave_management.services.leave_balance_services import LeaveBalanceService
from apps.hris.leave_management.api.serializers import LeaveBalanceCSVImportSerializer


class LeaveBalanceCSVImportView(APIView):
    """
    EN: Bulk import leave balances from CSV file.
    UZ: CSV fayl orqali ommaviy balans yuklash.
    """
    permission_classes = [IsAuthenticated, make_permission("leave.edit_balance")]

    @swagger_auto_schema(
        operation_description="Bulk import leave balances from CSV / CSV orqali ommaviy balans yuklash",
        responses={200: "Success/Failed summary"}
    )
    def post(self, request):
        serializer = LeaveBalanceCSVImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file = serializer.validated_data["file"]
        company_id = request.tenant.id
        adjusted_by_id = request.user.employee_id

        # CSV faylni o'qish
        try:
            decoded = file.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(decoded))

            # Ustunlarni tekshirish
            required_columns = {"employee_id", "leave_type_code", "year", "total_days"}
            if not required_columns.issubset(set(reader.fieldnames or [])):
                return Response(
                    {
                        "detail": (
                            f"CSV must have columns: {', '.join(required_columns)} / "
                            f"CSV da shu ustunlar bo'lishi kerak: {', '.join(required_columns)}"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            rows = list(reader)

            if not rows:
                return Response(
                    {"detail": "CSV file is empty. / CSV fayl bo'sh."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response(
                {"detail": f"Failed to read CSV file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Servisni chaqirish
        result = LeaveBalanceService.bulk_initialize_form_csv(
            rows=rows,
            company_id=company_id,
            adjusted_by_id=adjusted_by_id,
        )

        return Response(result, status=status.HTTP_200_OK)


class LeaveBalanceCSVTemplateView(APIView):
    """
        UZ: Ommaviy yuklash uchun CSV shablon yuklab oish
        ENG: Downlod CSV templste for bulk import
    """

    def get(self, request):
        from django.http import HttpResponse

        content = "employee_id,leave_type_code,year,total_days\n101,annual,2026,21\n102,sick,2026,10\n"
        response = HttpResponse(content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="leave_balance_template.csv"'
        return response

























