import logging
from django.db import transaction

from apps.hris.hris_core.models.employment import Employment, EmployeeAssignment

logger = logging.getLogger(__name__)


class EmploymentService:

    @staticmethod
    @transaction.atomic
    def create_employment(employee_id: int, **data)-> Employment:
        employment = Employment.objects.create(
            employee_id=employee_id, **data
        )

        logger.info(f"Employment creted for employee_id={employee_id}")
        return employment

    @staticmethod
    @transaction.atomic
    def update_employment(employment_id: int, employee_id: int, **data)-> Employment:
        employment = Employment.objects.filter(
            id=employment_id, employee_id=employee_id, is_deleted=False
        ).first()

        if not employment:
            raise ValueError("Employment not found.")

        for attr, value in data.items():
            setattr(employment, attr, value)

        employment.save()
        logger.info(f"Employment update: id={employment_id}")
        return employment

    @staticmethod
    @transaction.atomic
    def delete_employment(employment_id: int, employee_id: int)-> None:
        employment = Employment.objects.filter(
            id=employment_id, employee_id=employee_id, is_deleted=False
        ).first()

        if not employment:
            raise ValueError("Employment not found")

        employment.delete()
        logger.info(f"Employment, deleted: id ={employment_id}")



