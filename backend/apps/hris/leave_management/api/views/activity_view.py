from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

from ...selectors.selectors import LeaveSelector
from ..serializers import LeaveActivityLogSerializer
from internal_auth.services.permission_resolver import PermissionResolver


class LeaveActivityLogListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Ta'til so'rovlari tarixi (Activity Log)",
        responses={200: LeaveActivityLogSerializer(many=True)}
    )
    def get(self, request):
        company_id = request.tenant.id
        # 1. Ruxsatlarni PermissionResolver orqali olamiz
        perms = PermissionResolver.resolve(request.user.id, company_id)

        # Menejer yoki HR ekanligini aniqlaymiz
        is_manager = any(role in ["MANAGER", "HR_ADMIN"] for role in perms["roles"]) or \
                     "leave.view_all_logs" in perms["permissions"]

        # 2. Selectorni chaqiramiz
        # Menejer bo'lsa query_params'dan employee_id'ni oladi, bo'lmasa None
        logs = LeaveSelector.get_activity_logs(
            user=request.user,
            company_id=company_id,
            employee_id=request.query_params.get("employee_id") if is_manager else None,
            leave_request_id=request.query_params.get("leave_request_id"),
            action=request.query_params.get("action")
        )

        # 3. Serializatsiya va Response
        serializer = LeaveActivityLogSerializer(logs, many=True)
        return Response(serializer.data)