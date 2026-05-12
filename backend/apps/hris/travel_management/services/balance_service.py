import csv, io, logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.hris.travel_management.models import (
    BusinessTripBalance,
    BusinessTripBalanceAdjustment,
)

logger = logging.getLogger(__name__)


class BusinessTripBalanceService:

    @staticmethod
    @transaction.atomic
    def adjust_balance(
        balance_id: int,
        company_id: int,
        performed_by_id: int,
        adjustment_type: str,
        days: Decimal,
        reason: str = None,
    ) -> BusinessTripBalance:
        """
        HR tomonidan individual balans o'zgartirish.
        add → total_days oshadi
        deduct → total_days kamayadi
        """
        balance = BusinessTripBalance.objects.filter(
            id=balance_id, company_id=company_id,
        ).first()

        if not balance:
            raise ValueError("Business trip balance not found.")
        if days <= 0:
            raise ValidationError("Days must be a positive number.")
        if adjustment_type not in [
            BusinessTripBalanceAdjustment.AdjustmentTypeChoice.ADD,
            BusinessTripBalanceAdjustment.AdjustmentTypeChoice.DEDUCT,
        ]:
            raise ValidationError("Invalid adjustment type. Use 'add' or 'deduct'.")

        if adjustment_type == BusinessTripBalanceAdjustment.AdjustmentTypeChoice.ADD:
            balance.total_days += days
        else:
            if balance.total_days - days < 0:
                raise ValidationError("Cannot deduct more days than the total balance.")
            balance.total_days -= days

        balance.save()

        BusinessTripBalanceAdjustment.objects.create(
            balance=balance,
            performed_by_id=performed_by_id,
            adjustment_type=adjustment_type,
            days=days,
            reason=reason,
            company_id=company_id,
        )

        logger.info(f"Balance adjusted: id={balance_id}, type={adjustment_type}, days={days}")
        return balance


    @staticmethod
    @transaction.atomic
    def deduct_balance(
        employee_id: int,
        company_id: int,
        year: int,
        days: int,
    ) -> BusinessTripBalance:
        """
        HR approve qilganda avtomatik used_days oshirish.
        Balance yo'q bo'lsa — avtomatik yaratiladi.
        """
        balance, _ = BusinessTripBalance.objects.get_or_create(
            employee_id=employee_id,
            year=year,
            defaults={
                "company_id": company_id,
                "total_days": Decimal("0"),
                "used_days": Decimal("0"),
            }
        )
        balance.used_days += Decimal(days)
        balance.save()
        return balance


    @staticmethod
    @transaction.atomic
    def bulk_adjust(
        company_id: int,
        performed_by_id: int,
        adjustment_type: str,
        days: Decimal,
        reason: str = None,
        employee_ids: list = None,
    ) -> dict:
        """
        Bir vaqtda ko'p xodim balansini o'zgartirish.
        employee_ids bo'sh → barcha xodimlar.
        """
        current_year = timezone.now().year
        qs = BusinessTripBalance.objects.filter(
            company_id=company_id, year=current_year,
        )
        if employee_ids:
            qs = qs.filter(employee_id__in=employee_ids)

        results = {"success": [], "failed": []}
        for balance in qs:
            try:
                BusinessTripBalanceService.adjust_balance(
                    balance_id=balance.id,
                    company_id=company_id,
                    performed_by_id=performed_by_id,
                    adjustment_type=adjustment_type,
                    days=days, reason=reason,
                )
                results["success"].append(balance.employee_id)
            except Exception as e:
                results["failed"].append({"employee_id": balance.employee_id, "error": str(e)})

        return results


    @staticmethod
    @transaction.atomic
    def import_from_csv(
        company_id: int,
        performed_by_id: int,
        file,
    ) -> dict:
        """
        CSV fayldan balanslarni import qilish.
        Format: employee_id, adjustment_type, days, reason
        """
        results = {"success": [], "failed": [], "errors": []}
        current_year = timezone.now().year

        try:
            decoded = file.read().decode("utf-8")
            reader  = csv.DictReader(io.StringIO(decoded))
        except Exception as e:
            raise ValidationError(f"Invalid CSV file: {str(e)}")

        required_fields = {"employee_id", "adjustment_type", "days"}

        for row_num, row in enumerate(reader, start=2):
            missing = required_fields - set(row.keys())
            if missing:
                results["errors"].append({"row": row_num, "error": f"Missing: {missing}"})
                continue
            try:
                employee_id     = int(row["employee_id"])
                adjustment_type = row["adjustment_type"].strip().lower()
                days            = Decimal(row["days"].strip())
                reason          = row.get("reason", "").strip() or None

                balance, _ = BusinessTripBalance.objects.get_or_create(
                    employee_id=employee_id, year=current_year,
                    defaults={"company_id": company_id,
                              "total_days": Decimal("0"),
                              "used_days": Decimal("0")}
                )
                BusinessTripBalanceService.adjust_balance(
                    balance_id=balance.id, company_id=company_id,
                    performed_by_id=performed_by_id,
                    adjustment_type=adjustment_type,
                    days=days, reason=reason,
                )
                results["success"].append(employee_id)
            except Exception as e:
                results["failed"].append({"row": row_num, "error": str(e)})

        return results


    @staticmethod
    def get_csv_template() -> str:
        """CSV import uchun namuna template."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["employee_id", "adjustment_type", "days", "reason"])
        writer.writerow(["1", "add", "5", "Annual allocation"])
        writer.writerow(["2", "deduct", "2", "Correction"])
        return output.getvalue()