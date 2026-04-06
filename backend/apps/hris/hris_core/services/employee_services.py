import logging
from django.db import transaction
from apps.hris.hris_core.models.employee import Employee

logger = logging.getLogger(__name__)

class EmployeeService:
    @staticmethod
    @transaction.atomic
    def create_employee(company_id: int, **data)-> Employee:
        """
        U: Yangi hodim yaratish matig'i
        @transaction.atomic - agar bironta xato bo'lsa ( masalan location topilmasa )
        bazaga hech narsa saqalamaydi
        """
        employee = Employee.objects.create(company_id=company_id, **data)

        logger.info(f"employee created: {employee.first_name} {employee.last_name} (ID:{employee.employee_id})")
        return employee


    @staticmethod
    @transaction.atomic
    def update_employee(employee_id: int, company_id: int,  **data)-> Employee:
        """
        ENG: edit employee information
        UZB: Xodim malumotlarini taxrirlash
        """

        employee = Employee.objects.filter(id=employee_id, company_id=company_id).first()

        if not employee:
            logger.warning(f"Update field: Employee ID {employee_id} not found in Companiy {company_id}")
            raise ValueError('employee not found')

        for attr, value in data.items():
            setattr(employee, attr, value)

        employee.full_clean()
        employee.save()

        logger.info(f"Employee update: {employee.first_name} {employee.last_name} (ID: {employee.id})")
        return employee

    @staticmethod
    @transaction.atomic
    def delete_employee(employee_id:int, company_id)-> None:
        employee = Employee.objects.filter(
            id=employee_id, company_id=company_id, is_deleted=False
        ).first()
        if not employee:
            raise ValueError("Employee not found")
        employee.delete()






























