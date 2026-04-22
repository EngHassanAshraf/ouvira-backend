from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status


class LeavePDFExportTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    @patch("apps.hris.leave_management.services.leave_pdf_service._register_fonts")
    def test_approved_request_returns_pdf(self, mock_fonts):
        """
        ✅ APPROVED so'rov — PDF qaytarishi kerak.
        """
        mock_fonts.return_value = None

        # Approved leave request mock
        with patch("apps.hris.leave_management.models.LeaveRequest.objects") as mock_qs:
            mock_request = MagicMock()
            mock_request.status = "approved"
            mock_request.employee.first_name = "John"
            mock_request.employee.last_name = "Doe"
            mock_request.leave_type.name = "Annual Leave"
            mock_request.start_date = timezone.now().date()
            mock_request.end_date = timezone.now().date()
            mock_request.duration = 1
            mock_request.hr_approved_by = None
            mock_request.hr_approved_at = None
            mock_qs.select_related.return_value.filter.return_value.first.return_value = mock_request

            response = self.client.get(f"/api/leave-requests/1/export-pdf/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response["Content-Type"], "application/pdf")

    def test_pending_request_returns_400(self):
        """
        ❌ PENDING so'rov — 400 qaytarishi kerak.
        """
        with patch("apps.hris.leave_management.services.leave_pdf_service.LeaveRequest.objects") as mock_qs:
            mock_request = MagicMock()
            mock_request.status = "pending"
            mock_qs.select_related.return_value.filter.return_value.first.return_value = mock_request

            response = self.client.get(f"/api/leave-requests/1/export-pdf/")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_employee_request_returns_404(self):
        """
        ❌ Boshqa xodimning so'rovi — 404 qaytarishi kerak.
        """
        with patch("apps.hris.leave_management.models.LeaveRequest.objects") as mock_qs:
            mock_qs.filter.return_value.first.return_value = None

            response = self.client.get(f"/api/leave-requests/999/export-pdf/")
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)