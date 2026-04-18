import logging
from django.db import transaction
from django.utils import timezone

from apps.hris.hris_core.models.employee import Employee

logger = logging.getLogger(__name__)


class EmployeeService:

    @staticmethod
    @transaction.atomic
    def create_employee(company_id: int, **data) -> Employee:
        employee = Employee.objects.create(company_id=company_id, **data)
        logger.info(
            f"Employee created: {employee.full_name} (ID: {employee.employee_id})"
        )
        return employee

    @staticmethod
    @transaction.atomic
    def update_employee(employee_id: int, company_id: int, **data) -> Employee:
        employee = Employee.objects.filter(
            id=employee_id, company_id=company_id, is_deleted=False
        ).first()

        if not employee:
            logger.warning(
                f"Update failed: Employee {employee_id} not found in company {company_id}"
            )
            raise ValueError("Employee not found")

        for attr, value in data.items():
            setattr(employee, attr, value)

        employee.full_clean()
        employee.save()
        logger.info(f"Employee updated: {employee.full_name} (pk={employee.id})")
        return employee

    @staticmethod
    @transaction.atomic
    def delete_employee(employee_id: int, company_id: int) -> None:
        """Soft-delete (archive) an employee."""
        employee = Employee.objects.filter(
            id=employee_id, company_id=company_id, is_deleted=False
        ).first()
        if not employee:
            raise ValueError("Employee not found")

        employee.is_deleted = True
        employee.deleted_at = timezone.now()
        employee.save(update_fields=["is_deleted", "deleted_at"])
        logger.info(f"Employee archived: pk={employee_id}")

    @staticmethod
    @transaction.atomic
    def restore_employee(employee_id: int, company_id: int) -> Employee:
        """Restore a soft-deleted employee."""
        employee = Employee.all_objects.filter(
            id=employee_id, company_id=company_id, is_deleted=True
        ).first()
        if not employee:
            raise ValueError("Archived employee not found")

        employee.is_deleted = False
        employee.deleted_at = None
        employee.save(update_fields=["is_deleted", "deleted_at"])
        logger.info(f"Employee restored: pk={employee_id}")
        return employee
