import logging
from django.db.models import QuerySet
from apps.hris.leave_management.models import LeaveRequest, LeaveBalance

logger = logging.getLogger(__name__)


class LeaveSelector:

    @staticmethod
    def get_employee_requests(
        employee_id: int,
        status: str = None,
        leave_type_id: int = None,
        start_date=None,
        end_date=None,
        ordering: str = "-created_at",
    ) -> QuerySet:
        """
        Xodimning o'z so'rovlari ro'yxati.
        Filter + Sort qo'llab-quvvatlanadi.
        """
        qs = LeaveRequest.objects.filter(
            employee_id=employee_id,
            is_deleted=False,
        ).select_related("leave_type", "employee")

        # Filterlar
        if status:
            qs = qs.filter(status=status)
        if leave_type_id:
            qs = qs.filter(leave_type_id=leave_type_id)
        if start_date:
            qs = qs.filter(start_date__gte=start_date)
        if end_date:
            qs = qs.filter(end_date__lte=end_date)

        # Sort
        allowed_ordering = [
            "start_date", "-start_date",
            "end_date", "-end_date",
            "duration", "-duration",
            "status", "-status",
            "created_at", "-created_at",
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    @staticmethod
    def get_company_requests(
        company_id: int,
        status: str = None,
        leave_type_id: int = None,
        department_id: int = None,
        start_date=None,
        end_date=None,
        ordering: str = "-created_at",
    ) -> QuerySet:
        """
        Menejer uchun — kompaniyadagi barcha so'rovlar.
        Department, status, tur bo'yicha filter.
        """
        qs = LeaveRequest.objects.filter(
            employee__company_id=company_id,
            is_deleted=False,
        ).select_related("leave_type", "employee", "employee__department")

        if status:
            qs = qs.filter(status=status)
        if leave_type_id:
            qs = qs.filter(leave_type_id=leave_type_id)
        if department_id:
            qs = qs.filter(employee__department_id=department_id)
        if start_date:
            qs = qs.filter(start_date__gte=start_date)
        if end_date:
            qs = qs.filter(end_date__lte=end_date)

        allowed_ordering = [
            "start_date", "-start_date",
            "duration", "-duration",
            "status", "-status",
            "created_at", "-created_at",
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    @staticmethod
    def get_request_detail(
        leave_request_id: int,
        employee_id: int = None,
    ) -> LeaveRequest:
        """
        Bitta so'rov detail — activity log bilan.
        """
        qs = LeaveRequest.objects.filter(
            id=leave_request_id,
            is_deleted=False,
        ).select_related(
            "leave_type",
            "employee",
            "manager_approved_by",
            "hr_approved_by",
            "declined_by",
            "interrupted_by",
        ).prefetch_related("activity_logs")

        if employee_id:
            qs = qs.filter(employee_id=employee_id)

        request = qs.first()
        if not request:
            raise ValueError("Leave request not found.")
        return request

    @staticmethod
    def get_pending_for_manager(
        company_id: int,
        department_id: int = None,
    ) -> QuerySet:
        """
        Manager uchun — faqat PENDING so'rovlar.
        """
        qs = LeaveRequest.objects.filter(
            employee__company_id=company_id,
            status=LeaveRequest.StatusChoice.PENDING,
            is_deleted=False,
        ).select_related("leave_type", "employee", "employee__department")

        if department_id:
            qs = qs.filter(employee__department_id=department_id)

        return qs.order_by("start_date")

    @staticmethod
    def get_pending_for_hr(company_id: int) -> QuerySet:
        """
        HR Director uchun — faqat MANAGER_APPROVED so'rovlar.
        """
        return LeaveRequest.objects.filter(
            employee__company_id=company_id,
            status=LeaveRequest.StatusChoice.MANAGER_APPROVED,
            is_deleted=False,
        ).select_related(
            "leave_type", "employee",
            "manager_approved_by"
        ).order_by("manager_approved_at")

    @staticmethod
    def get_balance_summary(
        employee_id: int,
        year: int,
    ) -> QuerySet:
        """
        Xodimning barcha leave turlari bo'yicha balansi.
        """
        return LeaveBalance.objects.filter(
            employee_id=employee_id,
            year=year,
        ).select_related("leave_type")