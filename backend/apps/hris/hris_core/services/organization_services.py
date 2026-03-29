from django.db import transaction
from apps.hris.hris_core.models import Department, JobTitle

class OrganizationService:
    @staticmethod
    @transaction.atomic
    def create_department(name: str, company_id: int, parent_department_id: int = None, manager_id: int = None) -> Department:
        return Department.objects.create(
            name=name,
            company_id=company_id,
            parent_department_id=parent_department_id,
            manager_id=manager_id
        )

    @staticmethod
    @transaction.atomic
    def update_department(department_id: int, company_id:  int, **data)-> Department:
        department = Department.objects.filter(
            id=department_id, company_id=company_id, is_deleted=False
        ).first()

        if not department:
            raise ValueError("department not found")

        for attr, value, in data.items():
            setattr(department, attr,  value)

            department.save()
            return department


    @staticmethod
    @transaction.atomic
    def deleted_department(department_id: int, company_id: int)-> None:
        department = Department.objects.filter(
            id=department_id, company_id=company_id, is_deleted=False
        ).first()

        if not department:
            raise ValueError("Department not found.")

        department.delete()



    @staticmethod
    @transaction.atomic
    def create_job_title(title: str, company_id: int, description: str = "") -> JobTitle:
        return JobTitle.objects.create(
            title=title,
            company_id=company_id,
            description=description
        )