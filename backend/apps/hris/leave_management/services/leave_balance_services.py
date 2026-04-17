import logging
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.hris.leave_management.models import (
    LeaveBalance, LeaveBalanceAdjustment, LeaveType
)

logger = logging.getLogger(__name__)


class LeaveBalanceService:

    @staticmethod
    @transaction.atomic
    def initialize_balance(
        employee_id: int,
        leave_type_id: int,
        year: int,
        total_days: float,
    ) -> LeaveBalance:
        """
        Xodim uchun yangi balans yaratish.
        Yil boshida yoki yangi xodim qo'shilganda chaqiriladi.
        """
        balance, created = LeaveBalance.objects.get_or_create(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            year=year,
            defaults={"total_days": total_days}
        )
        if not created:
            logger.warning(f"Balance already exists: employee={employee_id}, year={year}")
        return balance

    @staticmethod
    @transaction.atomic
    def deduct_balance(
        employee_id: int,
        leave_type_id: int,
        year: int,
        days: float,
    ) -> LeaveBalance:
        """
        Tasdiqlanganda balansdan kunlar ayiriladi.
        """
        balance = LeaveBalanceService._get_balance(employee_id, leave_type_id, year)

        if balance.remaining_days < days:
            raise ValidationError(
                f"Insufficient leave balance. "
                f"Remaining: {balance.remaining_days}, Requested: {days}"
            )

        balance.used_days += days
        balance.save()

        logger.info(f"Balance deducted: employee={employee_id}, days={days}")
        return balance

    @staticmethod
    @transaction.atomic
    def refund_balance(
        employee_id: int,
        leave_type_id: int,
        year: int,
        days: float,
    ) -> LeaveBalance:
        """
        Cancel yoki Interrupt bo'lganda kunlar qaytariladi.
        """
        balance = LeaveBalanceService._get_balance(employee_id, leave_type_id, year)

        balance.used_days = max(0, balance.used_days - days)
        balance.save()

        logger.info(f"Balance refunded: employee={employee_id}, days={days}")
        return balance

    @staticmethod
    @transaction.atomic
    def adjust_balance(
        employee_id: int,
        leave_type_id: int,
        year: int,
        days: float,  # Musbat = qo'shish, Manfiy = ayirish
        adjusted_by_id: int,
        justification: str,
    ) -> LeaveBalance:
        """
        Menejer tomonidan qo'lda o'zgartirish (+/-).
        Justification majburiy.
        """
        if not justification or not justification.strip():
            raise ValidationError("Please provide a reason for the allowance adjustment.")

        balance = LeaveBalanceService._get_balance(employee_id, leave_type_id, year)

        balance.adjusted_days += days
        balance.save()

        # Tarix yozamiz
        LeaveBalanceAdjustment.objects.create(
            balance=balance,
            adjusted_by_id=adjusted_by_id,
            days=days,
            justification=justification,
        )

        logger.info(f"Balance adjusted: employee={employee_id}, days={days:+}")
        return balance

    @staticmethod
    def get_balance_summary(employee_id: int, year: int) -> list:
        """
        Xodimning barcha leave turlari bo'yicha balansi.
        """
        balances = LeaveBalance.objects.filter(
            employee_id=employee_id,
            year=year,
        ).select_related("leave_type")

        return [
            {
                "leave_type": b.leave_type.name,
                "leave_type_code": b.leave_type.code,
                "total_days": b.total_days,
                "used_days": b.used_days,
                "adjusted_days": b.adjusted_days,
                "remaining_days": b.remaining_days,
            }
            for b in balances
        ]

    # -------------------------------------------------------
    # Private helper
    # -------------------------------------------------------
    @staticmethod
    def _get_balance(employee_id: int, leave_type_id: int, year: int) -> LeaveBalance:
        balance = LeaveBalance.objects.filter(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            year=year,
        ).first()
        if not balance:
            raise ValueError("Leave balance not found for this employee and leave type.")
        return balance