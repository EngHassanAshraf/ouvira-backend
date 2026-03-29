from django.db.models import QuerySet
from apps.hris.hris_core.models.employee import Employee

class EmployeeSelector:
    @staticmethod
    def get_employee_by_company(company_id: int)-> QuerySet:
        """
        Kompaniyaning barcha o'chirilmagan hodimlar ro'yhatini olish
        """
        return Employee.objects.filter(
           company_id=company_id,
            is_deleted=False
        ).select_related('location', 'user')# locationni ham qo'shib olinadi Performans uchun

    @staticmethod
    def get_employee_detail(employee_id: int, company_id: int)-> Employee:
        """
        Bitta xodim haqida to'liq malumot.
        """
        return Employee.objects.get(id=employee_id, company_id=company_id)

    def get_detail(self, employee_id: int, company_id: int)-> Employee:
        return Employee.objects.select_related(
            "location", "department", "user"
        ).get(id=employee_id, company_id=company_id, is_deleted=False)
