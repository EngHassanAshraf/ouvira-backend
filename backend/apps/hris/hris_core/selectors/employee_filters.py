"""
Reusable employee queryset filter helper.
Used by both the API views and the export service — lives in the selector
layer so neither the service nor the view layer creates a circular import.
"""
from django.db.models import Q, QuerySet


def apply_employee_filters(queryset: QuerySet, params: dict) -> QuerySet:
    """
    Apply standard employee filters from a params mapping (query_params or dict).

    Supported keys:
        search            — full-text match across name / employee_id / email / phone / national_id
        nationality       — case-insensitive contains
        department        — exact FK id
        employment_status — match against Employment.status
    """
    nationality = params.get("nationality")
    department = params.get("department")
    employment_status = params.get("employment_status")
    search = params.get("search")

    if nationality:
        queryset = queryset.filter(nationality__icontains=nationality)
    if department:
        queryset = queryset.filter(department_id=department)
    if employment_status:
        queryset = queryset.filter(
            employments__status=employment_status,
            employments__is_deleted=False,
        ).distinct()
    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(employee_id__icontains=search)
            | Q(national_id__icontains=search)
            | Q(personal_email__icontains=search)
            | Q(contact_number__icontains=search)
        )
    return queryset
