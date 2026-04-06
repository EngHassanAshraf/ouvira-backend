from django.db.models import QuerySet
from apps.hris.hris_core.models import Department, JobTitle
from apps.hris.hris_core.models.organization import Position


class OrganizationSelector:
    @staticmethod
    def get_departments_by_company(company_id: int) -> QuerySet:
        """
        UZB: Kompaniyaning barcha bo'limlarini iyerarxiya va menejerlari bilan olish.
        """
        return Department.objects.filter(
            company_id=company_id
        ).select_related("parent_department", "manager")

    @staticmethod
    def get_job_titles_by_company(company_id: int) -> QuerySet:
        """
        UZB: Kompaniyaning barcha lavozimlarini olish.
        """
        return JobTitle.objects.filter(company_id=company_id)


    @staticmethod
    def get_positions_by_company(company_id: int) -> QuerySet:
        return Position.objects.filter(
            company_id=company_id, is_deleted=False, is_active=True
        ).select_related("job_title", "department", "location").order_by("department__name")


    @staticmethod
    def get_position_detail(position_id: int, company_id: int, )-> Position:
        return Position.objects.get(
            id=position_id, company_id=company_id, is_deleted=False
        )