import logging
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.hris.leave_management.models import (
    LeaveBalance, LeaveBalanceAdjustment, LeaveType
)
from hris_core.models import employee

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


    @staticmethod
    @transaction.atomic
    def bulk_initialize_form_csv(rows:list, company_id:int, adjusted_by_id:int, )->dict:
        """
        EN: Bulk initialize balance from csv rows
        UZ: csv qatorlaridan ommaviy balanse yaratish


        rows format:
        [
            {
                "employee_id": 101,
                "leave_type_code":"annual",
                "year": 2026,
                "total_days": 21
            },
            ...
        ]
        """

        from apps.hris.leave_management.models import LeaveBalance, LeaveType
        from apps.hris.hris_core.models import Employee

        success = 0
        failed = []

        for index, row in enumerate(rows, start=2):
            try:
                #1 Employee Tekshiruvi
                employee = Employee.objects.filter(
                    id=row.get("employee_id"),
                    company_id=company_id,
                    is_deleted=False,
                ).first()
                if not employee:
                    failed.append({
                        "row":index,
                        "error":f"Employee not found: {row.get('employee_id')}"
                    })
                    continue

                #2 Leave type tekshiruvi
                leave_type = LeaveType.objects.filter(
                    code=row.get("leave_type_code"),
                    is_active=True,
                    is_deleted=False,
                ).first()
                if not leave_type:
                    failed.append({
                        "row": index,
                        "error": f"Invalid leave type: {row.get('leave_type_code')}"
                    })
                    continue


                #3  year tekshiruvi
                year = row.get("year")
                if not year or not str(year).isdigit():
                    failed.append({
                        "row": index,
                        "error": f"Invalid year: {year}"
                    })
                    continue

                #4 Total das tekshiruv
                total_days = row.get("total_days")
                if total_days is None or float(total_days) < 0:
                    failed.append({
                        "row": index,
                        "error": f"Invalid total_days: {total_days}"
                    })
                    continue

                #5 Balans yaratish yokiy  ynagilash
                LeaveBalance.objects.update_or_create(
                    employee=employee,
                    leave_type=leave_type,
                    year=int(year),
                    defaults={"total_days": float(total_days)}
                )
                success +=1

            except Exception as e:
                failed.append({
                    "row": index,
                    "error": str(e)
                })
                continue

        return {
            "success": success,
            "failed": failed,
            "total": len(rows),
        }


























































