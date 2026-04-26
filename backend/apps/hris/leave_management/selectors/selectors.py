import logging

from django.db import models
from django.db.models import QuerySet
from twilio.rest.api.v2010.account import balance

from apps.hris.leave_management.models import LeaveRequest, LeaveBalance
from django.db.models import Q

logger = logging.getLogger(__name__)


class LeaveSelector:

    @staticmethod
    def get_employee_requests(
        employee_id: int,
        status: str = None,
        leave_type_ids: list=None,
        start_date=None,
        end_date=None,
        ordering: str = "-created_at",
        duration_min: int = None,
        duration_max: int = None,
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
        if leave_type_ids:
            qs = qs.filter(leave_type_id__in=leave_type_ids)
        if start_date:
            qs = qs.filter(start_date__gte=start_date)
        if end_date:
            qs = qs.filter(end_date__lte=end_date)
        if duration_min is not None:  # ← qo'shing
            qs = qs.filter(duration__gte=duration_min)
        if duration_max is not None:  # ← qo'shing
            qs = qs.filter(duration__lte=duration_max)

        # Sort
        allowed_ordering = [
            "leave_type__name", "-leave_type__name",
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
            company_id : int,
            status: str = None,
            leave_type_ids: list = None,  # ← o'zgardi
            start_date=None,
            end_date=None,
            duration_min: int = None,  # ← qo'shing
            duration_max: int = None,  # ← qo'shing
            ordering: str = "-created_at",
            department_id: int = None
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
        if leave_type_ids:
            qs = qs.filter(leave_type_id__in=leave_type_ids)
        if department_id:
            qs = qs.filter(employee__department_id=department_id)
        if start_date:
            qs = qs.filter(start_date__gte=start_date)
        if end_date:
            qs = qs.filter(end_date__lte=end_date)
        if duration_min is not None:  # ← qo'shing
            qs = qs.filter(duration__gte=duration_min)
        if duration_max is not None:  # ← qo'shing
            qs = qs.filter(duration__lte=duration_max)

        allowed_ordering = [
            "leave_type__name",
            "-leave_type__name",
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


    @staticmethod
    def get_activity_logs(
            user,
            company_id: int, employee_id:int=None,
            leave_request_id: int=None,
            action: str = None
    )-> QuerySet:
        """
        Activity Loglarni filtrlash
        Meneger hamma logni, xodim esa o'zinikini kjo'radi
        Filter activity logs.
        Managers can see all logs, while employees can only see their own.
        """
        from apps.hris.leave_management.models import LeaveActivityLog

        # Asosoiy query
        qs = LeaveActivityLog.objects.filter(
            leave_request__employee__company_id=company_id
        ).select_related("performed_by", "leave_request", "leave_request__employee")

        # 1. Access Control: Menejer bo'lmasa, faqat o'zi bajargan yoki o'zining arizasiga oid loglar
        # (Internal auth orqali rol tekshirish viewda bo'ladi, bu yerda qo'shimcha xavfsizlik)
        if not (user.is_staff or getattr(user, 'is_manager', False)):
            qs=qs.filter(
                Q(performed_by__user_id=user.id) |
                Q(leave_request__employee__user_id=user.id)
            )

        #qo'shimcha filterlar
        if employee_id:
            qs = qs.filter(leave_request__employee_id=employee_id)
        if leave_request_id:
            qs = qs.filter(leave_request_id=leave_request_id)
        if action:
            qs = qs.filter(action=action)

        return  qs


    @staticmethod
    def get_balance_adjustments(
            company_id: int,
            employee_id: int = None,
            leave_type_id: int = None,
            year: int =None
    )-> QuerySet:
        """
            EN: Retuen Balance adjustment history for a company
            UZ: Kompaniya bo'yicha balanse o"zgartirsh  tarixini qaytaradi
        """
        from apps.hris.leave_management.models import LeaveBalanceAdjustment

        qs = LeaveBalanceAdjustment.objects.filter(
            balance__employee__company_id=company_id,
            is_deleted=False,
        ).select_related(
            "balance__employee",
            "balance__leave_type",
            "adjusted_by",
        ).order_by("-create_at")

        if employee_id:
            qs = qs.filter(balance__employee_id=employee_id)
        if leave_type_id:
            qs = qs.filter(balance__leave_type_id=leave_type_id)
        if year:
            qs =qs.filter(balance__year=year)

        return qs
