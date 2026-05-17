from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from apps.access_control.permissions.IsAdminUser import IsAdminUser
from apps.hris.leave_management.services.leave_pdf_service import (
    LeavePDFService, LeavePDFFontError
)


class LeavePDFExportView(APIView):
    """
    GET — xodim o'z so'rovini PDF ga export qiladi.
    Faqat o'zining APPROVED so'rovi.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee_id = request.user.employee_id
        company_name = getattr(request.tenant, "name", "Company")

        # Faqat o'z so'rovi
        from apps.hris.leave_management.models import LeaveRequest
        leave_request = LeaveRequest.objects.filter(
            id=pk,
            employee_id=employee_id,
            is_deleted=False,
        ).first()

        if not leave_request:
            return Response(
                {"detail": "Leave request not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            buffer = LeavePDFService.generate(pk, company_name)
            response = HttpResponse(buffer, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="leave_request_{pk}.pdf"'
            return response
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ManagerLeavePDFExportView(APIView):
    """
    GET — menejer istalgan xodimning APPROVED so'rovini PDF ga export qiladi.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, pk):
        company_name = getattr(request.tenant, "name", "Company")

        try:
            buffer = LeavePDFService.generate(pk, company_name)
            response = HttpResponse(buffer, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="leave_request_{pk}.pdf"'
            return response
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)