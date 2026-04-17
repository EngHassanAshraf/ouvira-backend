"""
EmployeeFullCreateService
=========================
Handles the single-payload "create employee with all tabs" flow:
  1. Create Employee (personal information)
  2. Create Employment record (if provided)
  3. Create Allowances (if provided)
  4. Create Bank Detail (if provided)

All steps run inside a single atomic transaction so a failure in any
step rolls back the entire operation.
"""
import logging
from django.db import transaction

logger = logging.getLogger(__name__)


class EmployeeFullCreateService:

    @staticmethod
    @transaction.atomic
    def create(company_id: int, validated_data: dict) -> "Employee":  # noqa: F821
        from apps.hris.hris_core.models.employee import Employee
        from apps.hris.hris_core.models.employment import Employment
        from apps.hris.hris_core.models.employee_extensions import (
            EmployeeAllowance,
            EmployeeBankDetail,
        )

        # ── 1. Extract nested payloads ─────────────────────────────────────────
        employment_data = validated_data.pop("employment", None)
        allowances_data = validated_data.pop("allowances", [])
        bank_detail_data = validated_data.pop("bank_detail", None)

        # ── 2. Create Employee ─────────────────────────────────────────────────
        employee = Employee.objects.create(company_id=company_id, **validated_data)
        logger.info("FullCreate — Employee created: pk=%s", employee.pk)

        # ── 3. Create Employment ───────────────────────────────────────────────
        if employment_data:
            Employment.objects.create(employee=employee, **employment_data)
            logger.info("FullCreate — Employment created for employee pk=%s", employee.pk)

        # ── 4. Create Allowances ───────────────────────────────────────────────
        if allowances_data:
            EmployeeAllowance.objects.bulk_create([
                EmployeeAllowance(employee=employee, **a)
                for a in allowances_data
            ])
            logger.info(
                "FullCreate — %s allowances created for employee pk=%s",
                len(allowances_data), employee.pk,
            )

        # ── 5. Create Bank Detail ──────────────────────────────────────────────
        if bank_detail_data:
            EmployeeBankDetail.objects.create(employee=employee, **bank_detail_data)
            logger.info("FullCreate — Bank detail created for employee pk=%s", employee.pk)

        return employee
