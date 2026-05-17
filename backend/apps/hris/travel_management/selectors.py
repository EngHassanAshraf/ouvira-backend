import logging

from django.db.models import QuerySet, Q

from apps.hris.travel_management.models import (
    BusinessTripRequest,
    BusinessTripBalance,
    BusinessTripActivityLog,
    BusinessTripBalanceAdjustment,
    BusinessTripBenefit,
)

logger = logging.getLogger(__name__)


class BusinessTripSelector:

    @staticmethod
    def get_employee_requests(
        employee_id: int,
        status: str = None,
        destination: str = None,
        start_date=None,
        end_date=None,
        duration_min: int = None,
        duration_max: int = None,
        ordering: str = "-created_at",
    ) -> QuerySet:
        qs = BusinessTripRequest.objects.filter(
            employee_id=employee_id,
            is_deleted=False,
        ).select_related("employee", "created_by").prefetch_related("benefits")

        if status:
            qs = qs.filter(status=status)
        if destination:
            qs = qs.filter(destination__icontains=destination)
        if start_date:
            qs = qs.filter(start_date__gte=start_date)
        if end_date:
            qs = qs.filter(end_date__lte=end_date)
        if duration_min is not None:
            qs = qs.filter(duration__gte=duration_min)
        if duration_max is not None:
            qs = qs.filter(duration__lte=duration_max)

        allowed_ordering = [
            "start_date", "-start_date",
            "end_date", "-end_date",
            "duration", "-duration",
            "status", "-status",
            "destination", "-destination",
            "created_at", "-created_at",
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        return qs

    @staticmethod
    def get_company_requests(
        company_id: int,
        status: str = None,
        employee_id: int = None,
        department_id: int = None,
        destination: str = None,
        start_date=None,
        end_date=None,
        ordering: str = "-created_at",
    ) -> QuerySet:
        qs = BusinessTripRequest.objects.filter(
            company_id=company_id,
            is_deleted=False,
        ).select_related(
            "employee", "employee__department",
            "created_by", "manager_approved_by", "hr_approved_by",
        ).prefetch_related("benefits")

        if status:
            qs = qs.filter(status=status)
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if department_id:
            qs = qs.filter(employee__department_id=department_id)
        if destination:
            qs = qs.filter(destination__icontains=destination)
        if start_date:
            qs = qs.filter(start_date__gte=start_date)
        if end_date:
            qs = qs.filter(end_date__lte=end_date)

        allowed_ordering = [
            "start_date", "-start_date",
            "end_date", "-end_date",
            "duration", "-duration",
            "status", "-status",
            "created_at", "-created_at",
            "employee__full_name", "-employee__full_name",
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        return qs

    @staticmethod
    def get_request_detail(
        trip_request_id: int,
        employee_id: int = None,
    ) -> BusinessTripRequest:
        qs = BusinessTripRequest.objects.filter(
            id=trip_request_id,
            is_deleted=False,
        ).select_related(
            "employee", "created_by",
            "manager_approved_by", "hr_approved_by",
            "declined_by", "interrupted_by",
        ).prefetch_related(
            "benefits",
            "activity_logs",
            "activity_logs__performed_by",
        )

        if employee_id:
            qs = qs.filter(employee_id=employee_id)

        trip = qs.first()
        if not trip:
            raise ValueError("Business trip request not found.")
        return trip

    @staticmethod
    def get_pending_for_manager(
        company_id: int,
        department_id: int = None,
    ) -> QuerySet:
        qs = BusinessTripRequest.objects.filter(
            company_id=company_id,
            status=BusinessTripRequest.StatusChoice.PENDING,
            is_deleted=False,
        ).select_related("employee", "employee__department")

        if department_id:
            qs = qs.filter(employee__department_id=department_id)
        return qs.order_by("start_date")

    @staticmethod
    def get_pending_for_hr(company_id: int) -> QuerySet:
        return BusinessTripRequest.objects.filter(
            company_id=company_id,
            status=BusinessTripRequest.StatusChoice.MANAGER_APPROVED,
            is_deleted=False,
        ).select_related(
            "employee", "manager_approved_by",
        ).order_by("manager_approved_at")

    @staticmethod
    def get_balance_list(
        company_id: int,
        year: int,
        employee_id: int = None,
        department_id: int = None,
        ordering: str = "-total_days",
    ) -> QuerySet:
        qs = BusinessTripBalance.objects.filter(
            company_id=company_id,
            year=year,
        ).select_related("employee", "employee__department")

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if department_id:
            qs = qs.filter(employee__department_id=department_id)

        allowed_ordering = [
            "total_days", "-total_days",
            "used_days", "-used_days",
            "employee__full_name", "-employee__full_name",
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        return qs

    @staticmethod
    def get_balance_detail(
        balance_id: int,
        company_id: int,
    ) -> BusinessTripBalance:
        balance = BusinessTripBalance.objects.filter(
            id=balance_id,
            company_id=company_id,
        ).select_related("employee").prefetch_related(
            "adjustments", "adjustments__performed_by",
        ).first()

        if not balance:
            raise ValueError("Business trip balance not found.")
        return balance

    @staticmethod
    def get_employee_balance(
        employee_id: int,
        year: int,
    ) -> BusinessTripBalance:
        balance = BusinessTripBalance.objects.filter(
            employee_id=employee_id,
            year=year,
        ).first()

        if not balance:
            raise ValueError("Business trip balance not found.")
        return balance

    @staticmethod
    def get_balance_adjustments(
        company_id: int,
        employee_id: int = None,
        year: int = None,
        adjustment_type: str = None,
        ordering: str = "-created_at",
    ) -> QuerySet:
        qs = BusinessTripBalanceAdjustment.objects.filter(
            company_id=company_id,
        ).select_related("balance__employee", "performed_by")

        if employee_id:
            qs = qs.filter(balance__employee_id=employee_id)
        if year:
            qs = qs.filter(balance__year=year)
        if adjustment_type:
            qs = qs.filter(adjustment_type=adjustment_type)

        allowed_ordering = [
            "created_at", "-created_at",
            "days", "-days",
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        return qs

    @staticmethod
    def get_benefits(company_id: int) -> QuerySet:
        return BusinessTripBenefit.objects.filter(
            company_id=company_id,
            is_deleted=False,
        ).order_by("is_fixed", "name")