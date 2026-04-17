from django.db.models import QuerySet
from apps.hris.leave_management.models import LeaveType, LeaveRequest


class LeaveTypeSelector:

    @staticmethod
    def get_all_active() -> QuerySet:
        return LeaveType.objects.filter(is_deleted=False).order_by("name")


class LeaveRequestSelector:

    @staticmethod
    def get_all(company_employee_ids: list = None) -> QuerySet:
        """
        Return leave requests with optimised joins.
        Optionally scoped to a list of employee IDs for tenant isolation.
        """
        qs = (
            LeaveRequest.objects.filter(is_deleted=False)
            .select_related("employee", "leave_type", "approved_by")
            .order_by("-created_at")
        )
        if company_employee_ids is not None:
            qs = qs.filter(employee_id__in=company_employee_ids)
        return qs

    @staticmethod
    def get_by_employee(employee_id: int) -> QuerySet:
        return (
            LeaveRequest.objects.filter(employee_id=employee_id, is_deleted=False)
            .select_related("leave_type", "approved_by")
            .order_by("-created_at")
        )
