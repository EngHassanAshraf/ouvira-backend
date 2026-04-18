import logging

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from ..models import UserCompanyRole

logger = logging.getLogger(__name__)


class IsAdminUser(BasePermission):
    """
    Grants access only to users who hold an 'admin' role in the target company.

    Company resolution order:
      1. request.data["company"]   (POST body)
      2. request.query_params["company"]  (GET/DELETE query param)
      3. request.tenant.id         (tenant-scoped request)
    """

    message = "You are not authorized to perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        company_id = (
            request.data.get("company")
            or request.query_params.get("company")
            or getattr(getattr(request, "tenant", None), "id", None)
        )

        if not company_id:
            return False

        try:
            return UserCompanyRole.objects.filter(
                user_company__user=request.user,
                user_company__company=int(company_id),
                user_company__is_active=True,
                user_company__is_deleted=False,
                role__role__iexact="admin",
                role__is_deleted=False,
                is_deleted=False,
            ).exists()
        except (ValueError, TypeError):
            logger.warning(
                "IsAdminUser: invalid company_id=%r for user=%s",
                company_id,
                getattr(request.user, "pk", "?"),
            )
            return False
        except Exception:
            logger.exception("IsAdminUser: unexpected error during permission check")
            return False
