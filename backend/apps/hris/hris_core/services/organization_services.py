from django.db import transaction
from apps.hris.hris_core.models import Department, JobTitle
from apps.hris.hris_core.models.organization import Position


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
    def delete_department(department_id: int, company_id: int)-> None:
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

    @staticmethod
    @transaction.atomic
    def update_job_title(job_title_id: int, company_id: int, **data)-> JobTitle:
        job_title = JobTitle.objects.filter(
            id=job_title_id, company_id=company_id, is_deleted=False
        ).first()

        if not job_title:
            raise ValueError("Lob title not found")

        for attr, value in data.items():
            setattr(job_title, attr,value)

        job_title.save()
        return job_title


    @staticmethod
    @transaction.atomic
    def delete_job_title(job_title_id: int, company_id: int)-> None:
        job_title  = JobTitle.objects.filter(
            id=job_title_id, company_id=company_id, is_deleted=False
        ).first()

        if not job_title:
            raise ValueError("JobTitle not found")

        job_title.delete()


    @staticmethod
    @transaction.atomic
    def create_position(company_id: int, **data)-> Position:
        position = Position.objects.create(
            company_id=company_id, **data
        )
        return position


    @staticmethod
    @transaction.atomic
    def update_position(position_id: int, company_id: int, **data)-> Position:
        position =Position.objects.filter(
            id=position_id, company_id=company_id, is_deleted=False
        ).first()

        if not position:
            raise ValueError("Position not found.")

        for attr , value in data.items():
            setattr(position,attr, value)

        position.save()
        return position

    @staticmethod
    @transaction.atomic
    def delete_position(position_id: int, company_id: int)-> None:
        position = Position.objects.filter(
            id=position_id, company_id=company_id, is_deleted=False
        ).first()

        if not position:
            raise ValueError("Position not found")

        position.delete()

































