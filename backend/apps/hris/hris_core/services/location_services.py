from django.db import transaction
from apps.hris.hris_core.models import Location

class LocationService:
    @staticmethod
    @transaction.atomic
    def create_location(name: str, company_id: int, address: str ="", city: str="", is_active=True) -> Location:
        return Location.objects.create(
            name=name,
            company_id=company_id,
            address=address,
            city=city,
            is_active=is_active
        )