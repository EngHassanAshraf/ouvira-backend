from django.db.models import QuerySet
from apps.hris.hris_core.models.employment import Employment


class EmploymentSelector:

    @staticmethod
    def get_by_employee(employee_id: int)-> QuerySet:
        """
        Xodimning barcha employmen tyozuvlarini olish.
        Obtain all employee employment records.
        """
        return Employment.objects.filter(
            employee_id=employee_id, is_deleted=False
        ).order_by("-created_at")

    @staticmethod
    def get_detail(employment_id: int, employee_id: int)-> Employment:
        """
        Bittada employment yozuvini olish
        Get employment records in one go
        """

        return Employment.objects.get(
            id=employment_id, employee_id=employee_id, is_deleted=False
        )