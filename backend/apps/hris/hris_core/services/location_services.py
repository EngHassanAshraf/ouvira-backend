from django.db import transaction
from django.template.defaultfilters import first

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

    @staticmethod
    @transaction.atomic
    def update_location(location_id: int, company_id: int, **data)-> Location:
        location = Location.objects.filter(
            id=location_id, company_id=company_id, is_delete=False
        ).first()

        if not location:
            raise ValueError("location not found ")

        for attr, value, in data.item():
            setattr(location, attr, value)

        location.save()
        return location

    @staticmethod
    @transaction.atomic
    def delete_location(location_id: int, company_id: int) -> None:
        location = Location.objects.filter(
            id=location_id, company_id=company_id, is_deleted=False
        ).first()

        if not location:
            raise ValueError("Location not found.")

        location.delete()