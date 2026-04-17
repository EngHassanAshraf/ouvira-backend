from django.db.models import QuerySet
from apps.hris.travel_management.models import TravelRequest


class TravelRequestSelector:

    @staticmethod
    def get_all(employee_id: int = None) -> QuerySet:
        """Return travel requests with optimised joins, optionally filtered by employee."""
        qs = (
            TravelRequest.objects.filter(is_deleted=False)
            .select_related("employee")
            .order_by("-created_at")
        )
        if employee_id is not None:
            qs = qs.filter(employee_id=employee_id)
        return qs
