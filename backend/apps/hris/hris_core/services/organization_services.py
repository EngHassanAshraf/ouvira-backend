from django.db import transaction
from apps.hris.hris_core.models import Department, JobTitle

class OrganizationService:
    @staticmethod
    @transaction.atomic
    def create_department(name: str, companiy_id: int, parent_department_id: int = None, manager_id: int = None) -> Department:
        return Department.objects.create(
            name=name,
            companiy_id=companiy_id,
            parent_department_id=parent_department_id,
            manager_id=manager_id
        )

    @staticmethod
    @transaction.atomic
    def create_job_title(title: str, company_id: int, description: str = "") -> JobTitle:
        return JobTitle.objects.create(
            title=title,
            company_id=company_id,
            description=description
        )