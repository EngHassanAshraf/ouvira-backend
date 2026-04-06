from django.db.models import QuerySet
from apps.hris.hris_core.models import Location

class LocationSelector:
    @staticmethod
    def get_locations_by_company(company_id: int) -> QuerySet:
        """
        UZB: Kompaniyaning barcha AKTIV va o'chirilmagan filiallarini olish.
        """
        return Location.objects.filter(
            company_id=company_id,
            is_deleted=False,
            is_active=True
        )