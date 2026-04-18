"""
HasModulePermission
===================
A reusable DRF permission class that checks whether the authenticated user
holds a role (in the current tenant company) that has a specific permission
code granted via RolePermission.

Usage in a view:
    from apps.access_control.permissions.HasModulePermission import make_permission

    class LeaveRequestApproveApiView(APIView):
        permission_classes = [IsAuthenticated, make_permission("leave.approve_request")]

The permission code must exist in the Permission table and be linked to the
user's role via RolePermission with granted=True.
"""
import logging
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


def make_permission(required_code: str):
    """
    Factory that returns a DRF BasePermission subclass checking for
    the given permission code.

    Args:
        required_code: e.g. "leave.approve_request", "employee.bulk_archive"
    """

    class _Permission(BasePermission):
        message = f"You do not have the '{required_code}' permission."
        code = required_code

        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False

            company_id = getattr(getattr(request, "tenant", None), "id", None)
            if not company_id:
                return False

            try:
                from apps.access_control.models import UserCompanyRole, RolePermission

                # Get all role IDs the user holds in this company
                role_ids = UserCompanyRole.objects.filter(
                    user_company__user=request.user,
                    user_company__company_id=company_id,
                    user_company__is_active=True,
                    user_company__is_deleted=False,
                    is_deleted=False,
                ).values_list("role_id", flat=True)

                if not role_ids:
                    return False

                # Check if any of those roles have this permission granted
                return RolePermission.objects.filter(
                    role_id__in=role_ids,
                    permission__code=required_code,
                    permission__is_deleted=False,
                    granted=True,
                    is_deleted=False,
                ).exists()

            except Exception:
                logger.exception(
                    "HasModulePermission: unexpected error checking code=%s user=%s",
                    required_code,
                    getattr(request.user, "pk", "?"),
                )
                return False

    _Permission.__name__ = f"HasPermission_{required_code.replace('.', '_')}"
    _Permission.__qualname__ = _Permission.__name__
    return _Permission
