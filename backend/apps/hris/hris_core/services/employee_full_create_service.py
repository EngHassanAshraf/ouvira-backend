"""
EmployeeFullCreateService
=========================
Handles the single-payload "create employee with all tabs" flow:
  1. Create Employee (personal information + job details)
  2. Optionally create CustomUser and link it (when is_system_user=True)
  3. Create Employment record (if provided)
  4. Create Allowances (if provided)
  5. Create Bank Detail (if provided)
  6. Create Business Trip Balance (if provided)

All steps run inside a single atomic transaction.
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
            EmployeeBusinessTripBalance,
        )

        # ── 1. Extract nested / non-model payloads ─────────────────────────────
        employment_data         = validated_data.pop("employment", None)
        allowances_data         = validated_data.pop("allowances", [])
        bank_detail_data        = validated_data.pop("bank_detail", None)
        business_trip_data      = validated_data.pop("business_trip_balance", None)
        password                = validated_data.pop("password", None)
        validated_data.pop("password_confirm", None)  # already validated, discard

        is_system_user = validated_data.get("is_system_user", False)

        # ── 2. Create Employee ─────────────────────────────────────────────────
        employee = Employee.objects.create(company_id=company_id, **validated_data)
        logger.info("FullCreate — Employee created: pk=%s", employee.pk)

        # ── 3. Create system user account (if requested) ───────────────────────
        if is_system_user and password:
            user = EmployeeFullCreateService._create_system_user(
                employee=employee,
                password=password,
            )
            employee.user_id = user.pk
            employee.save(update_fields=["user_id"])
            logger.info(
                "FullCreate — System user created: user_pk=%s for employee pk=%s",
                user.pk, employee.pk,
            )

        # ── 4. Create Employment ───────────────────────────────────────────────
        if employment_data:
            Employment.objects.create(employee=employee, **employment_data)
            logger.info("FullCreate — Employment created for employee pk=%s", employee.pk)

        # ── 5. Create Allowances ───────────────────────────────────────────────
        if allowances_data:
            EmployeeAllowance.objects.bulk_create([
                EmployeeAllowance(employee=employee, **a)
                for a in allowances_data
            ])
            logger.info(
                "FullCreate — %s allowances created for employee pk=%s",
                len(allowances_data), employee.pk,
            )

        # ── 6. Create Bank Detail ──────────────────────────────────────────────
        if bank_detail_data:
            EmployeeBankDetail.objects.create(employee=employee, **bank_detail_data)
            logger.info("FullCreate — Bank detail created for employee pk=%s", employee.pk)

        # ── 7. Create Business Trip Balance ───────────────────────────────────
        if business_trip_data:
            EmployeeBusinessTripBalance.objects.create(
                employee=employee, **business_trip_data
            )
            logger.info(
                "FullCreate — Business trip balance created for employee pk=%s", employee.pk
            )

        return employee

    @staticmethod
    def _create_system_user(employee: "Employee", password: str):  # noqa: F821
        """
        Create a CustomUser account linked to this employee.
        Uses work_email if available, otherwise generates a username from employee_id.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        username = employee.work_email or f"emp_{employee.employee_id}"
        email = employee.work_email or ""

        # Avoid duplicate usernames
        if User.objects.filter(username=username).exists():
            username = f"emp_{employee.employee_id}_{employee.pk}"

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            full_name=employee.full_name,
            is_active=True,
        )
        return user
