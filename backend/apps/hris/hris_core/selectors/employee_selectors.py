from django.db.models import QuerySet, Prefetch
from apps.hris.hris_core.models.employee import Employee
from apps.hris.hris_core.models.employment import Employment


class EmployeeSelector:

    @staticmethod
    def get_employee_by_company(
        company_id: int,
        include_deleted: bool = False,
    ) -> QuerySet:
        """Return all employees for a company with optimised joins."""
        qs = Employee.objects.filter(company_id=company_id)
        if not include_deleted:
            qs = qs.filter(is_deleted=False)

        return qs.select_related(
            "location",
            "department",
            "reporting_manager",
        ).prefetch_related(
            Prefetch(
                "employments",
                queryset=Employment.objects.filter(is_deleted=False).order_by(
                    "-created_at"
                ),
                to_attr="active_employments",
            )
        )

    @staticmethod
    def get_archived_employees(company_id: int) -> QuerySet:
        """Return soft-deleted employees (archive/bin view)."""
        return (
            Employee.all_objects.filter(company_id=company_id, is_deleted=True)
            .select_related("location", "department", "reporting_manager")
            .order_by("-deleted_at")
        )

    @staticmethod
    def get_employee_detail(employee_id: int, company_id: int) -> Employee:
        return (
            Employee.objects.select_related(
                "location",
                "department",
                "reporting_manager",
            )
            .prefetch_related(
                "employments",
                "leave_balances__leave_type",
                "allowances",
                "costs",
                "documents",
            )
            .get(id=employee_id, company_id=company_id, is_deleted=False)
        )
