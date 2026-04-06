from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from ..models import UserCompanyRole, UserCompany, Role

class IsAdminUser(BasePermission):
    message = "You're not Authorized"

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Check if user is admin in the target company
        # Verify user is admin in this company through access_control models

        # Early return if user is not authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check both request body (POST) and query params (DELETE)
        company_id = request.data.get("company") or request.query_params.get("company")or getattr(request.tenant, "id", None)

        # Early return if company_id is missing
        if not company_id:
            return False

        print(
            "user_company", 
            UserCompany.objects.filter(user=request.user),
        )

        print("user_company_role", UserCompanyRole.objects.filter(user_company__user=request.user.id, user_company__company=int(company_id)))
        print("role", Role.objects.filter(role__iexact="admin", is_deleted=False))

        try:
            is_admin = UserCompanyRole.objects.filter(
                user_company__user=request.user,
                user_company__company=int(company_id),
                user_company__is_active=True,  # Check if UserCompany is active
                user_company__is_deleted=False,  # Filter soft-deleted UserCompany
                role__role__iexact="admin",  # Case-insensitive role check
                role__is_deleted=False,  # Filter soft-deleted Role
                is_deleted=False,  # Filter soft-deleted UserCompanyRole
            ).exists()
            return is_admin
        except Exception:
            # Return False on any error (database, etc.)
            return False
