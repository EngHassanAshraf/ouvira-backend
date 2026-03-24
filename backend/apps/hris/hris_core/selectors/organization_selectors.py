from django.db.models import QuerySet
from apps.hris.hris_core.models import Department, JobTitle

class OrganizationSelector:
    @staticmethod
    def get_departments_by_company(company_id: int) -> QuerySet:
        """
        UZB: Kompaniyaning barcha bo'limlarini iyerarxiya va menejerlari bilan olish.
        """
        return Department.objects.filter(
            companiy_id=company_id
        ).select_related("parent_department", "manager")

    @staticmethod
    def get_job_titles_by_company(company_id: int) -> QuerySet:
        """
        UZB: Kompaniyaning barcha lavozimlarini olish.
        """
        return JobTitle.objects.filter(company_id=company_id)