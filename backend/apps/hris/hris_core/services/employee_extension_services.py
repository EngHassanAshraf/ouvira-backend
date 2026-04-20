import logging
from django.db import transaction

from apps.hris.hris_core.models.employee_extensions import (
    EmployeeLeaveBalance,
    EmployeeAllowance,
    EmployeeBankDetail,
    EmployeeCost,
    EmployeeDocument,
)

logger = logging.getLogger(__name__)


# ── Leave Balance ──────────────────────────────────────────────────────────────

class EmployeeLeaveBalanceService:

    @staticmethod
    @transaction.atomic
    def set_balance(employee_id: int, leave_type_id: int, **data) -> EmployeeLeaveBalance:
        balance, _ = EmployeeLeaveBalance.objects.update_or_create(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            defaults=data,
        )
        logger.info(f"Leave balance set: employee={employee_id}, leave_type={leave_type_id}")
        return balance

    @staticmethod
    @transaction.atomic
    def adjust_balance(balance_id: int, employee_id: int, **data) -> EmployeeLeaveBalance:
        balance = EmployeeLeaveBalance.objects.filter(
            id=balance_id, employee_id=employee_id, is_deleted=False
        ).first()
        if not balance:
            raise ValueError("Leave balance not found")
        for attr, value in data.items():
            setattr(balance, attr, value)
        balance.save()
        return balance

    @staticmethod
    @transaction.atomic
    def delete_balance(balance_id: int, employee_id: int) -> None:
        balance = EmployeeLeaveBalance.objects.filter(
            id=balance_id, employee_id=employee_id, is_deleted=False
        ).first()
        if not balance:
            raise ValueError("Leave balance not found")
        balance.is_deleted = True
        balance.save(update_fields=["is_deleted"])


# ── Allowance ──────────────────────────────────────────────────────────────────

class EmployeeAllowanceService:

    @staticmethod
    @transaction.atomic
    def create_allowance(employee_id: int, **data) -> EmployeeAllowance:
        allowance = EmployeeAllowance.objects.create(employee_id=employee_id, **data)
        logger.info(f"Allowance created: employee={employee_id}, name={allowance.name}")
        return allowance

    @staticmethod
    @transaction.atomic
    def update_allowance(allowance_id: int, employee_id: int, **data) -> EmployeeAllowance:
        allowance = EmployeeAllowance.objects.filter(
            id=allowance_id, employee_id=employee_id, is_deleted=False
        ).first()
        if not allowance:
            raise ValueError("Allowance not found")
        for attr, value in data.items():
            setattr(allowance, attr, value)
        allowance.save()
        return allowance

    @staticmethod
    @transaction.atomic
    def delete_allowance(allowance_id: int, employee_id: int) -> None:
        allowance = EmployeeAllowance.objects.filter(
            id=allowance_id, employee_id=employee_id, is_deleted=False
        ).first()
        if not allowance:
            raise ValueError("Allowance not found")
        allowance.is_deleted = True
        allowance.save(update_fields=["is_deleted"])


# ── Bank Detail ────────────────────────────────────────────────────────────────

class EmployeeBankDetailService:

    @staticmethod
    @transaction.atomic
    def set_bank_detail(employee_id: int, **data) -> EmployeeBankDetail:
        detail, _ = EmployeeBankDetail.objects.update_or_create(
            employee_id=employee_id,
            defaults=data,
        )
        logger.info(f"Bank detail set: employee={employee_id}")
        return detail

    @staticmethod
    @transaction.atomic
    def delete_bank_detail(employee_id: int) -> None:
        detail = EmployeeBankDetail.objects.filter(
            employee_id=employee_id, is_deleted=False
        ).first()
        if not detail:
            raise ValueError("Bank detail not found")
        detail.is_deleted = True
        detail.save(update_fields=["is_deleted"])


# ── Employee Cost ──────────────────────────────────────────────────────────────

class EmployeeCostService:

    @staticmethod
    @transaction.atomic
    def create_cost(employee_id: int, **data) -> EmployeeCost:
        cost = EmployeeCost.objects.create(employee_id=employee_id, **data)
        logger.info(f"Cost created: employee={employee_id}, type={cost.cost_type}")
        return cost

    @staticmethod
    @transaction.atomic
    def update_cost(cost_id: int, employee_id: int, **data) -> EmployeeCost:
        cost = EmployeeCost.objects.filter(
            id=cost_id, employee_id=employee_id, is_deleted=False
        ).first()
        if not cost:
            raise ValueError("Cost not found")
        for attr, value in data.items():
            setattr(cost, attr, value)
        cost.save()
        return cost

    @staticmethod
    @transaction.atomic
    def delete_cost(cost_id: int, employee_id: int) -> None:
        cost = EmployeeCost.objects.filter(
            id=cost_id, employee_id=employee_id, is_deleted=False
        ).first()
        if not cost:
            raise ValueError("Cost not found")
        cost.is_deleted = True
        cost.save(update_fields=["is_deleted"])


# ── Employee Document ──────────────────────────────────────────────────────────

class EmployeeDocumentService:

    @staticmethod
    @transaction.atomic
    def upload_document(employee_id: int, file, file_name: str = "") -> EmployeeDocument:
        doc = EmployeeDocument.objects.create(
            employee_id=employee_id,
            file=file,
            file_name=file_name or file.name,
        )
        logger.info(f"Document uploaded: employee={employee_id}, file={doc.file_name}")
        return doc

    @staticmethod
    @transaction.atomic
    def delete_document(document_id: int, employee_id: int) -> None:
        doc = EmployeeDocument.objects.filter(
            id=document_id, employee_id=employee_id, is_deleted=False
        ).first()
        if not doc:
            raise ValueError("Document not found")
        doc.is_deleted = True
        doc.save(update_fields=["is_deleted"])


# ── Business Trip Balance ──────────────────────────────────────────────────────

class EmployeeBusinessTripBalanceService:

    @staticmethod
    @transaction.atomic
    def set_balance(employee_id: int, **data) -> "EmployeeBusinessTripBalance":  # noqa: F821
        from apps.hris.hris_core.models.employee_extensions import EmployeeBusinessTripBalance
        balance, _ = EmployeeBusinessTripBalance.objects.update_or_create(
            employee_id=employee_id,
            defaults=data,
        )
        logger.info(f"Business trip balance set: employee={employee_id}")
        return balance

    @staticmethod
    def delete_balance(employee_id: int) -> None:
        from apps.hris.hris_core.models.employee_extensions import EmployeeBusinessTripBalance
        try:
            balance = EmployeeBusinessTripBalance.objects.get(employee_id=employee_id, is_deleted=False)
            balance.is_deleted = True
            balance.save(update_fields=["is_deleted"])
        except EmployeeBusinessTripBalance.DoesNotExist:
            raise ValueError(f"Business trip balance not found for employee {employee_id}")
