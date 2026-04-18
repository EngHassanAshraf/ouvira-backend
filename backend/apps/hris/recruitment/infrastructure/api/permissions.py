"""
Recruitment RBAC permission classes.

All classes check that the authenticated user holds a specific role
in the tenant company (resolved from request.tenant.id).

Role names are checked case-insensitively against UserCompanyRole.role.role.

Usage in ViewSets:
    permission_classes = [IsAuthenticated, IsHROrAdmin]
"""
import logging

from rest_framework.permissions import BasePermission

from apps.access_control.models import UserCompanyRole

logger = logging.getLogger(__name__)

# ── Helpers ────────────────────────────────────────────────────────────────────


def _get_company_id(request):
    """Resolve company_id: query param → request body → tenant."""
    return (
        request.query_params.get("company")
        or request.data.get("company")
        or getattr(getattr(request, "tenant", None), "id", None)
    )


def _has_role(request, *role_names):
    """
    Return True if the authenticated user holds ANY of the given roles
    in the resolved company.
    """
    if not request.user or not request.user.is_authenticated:
        return False

    company_id = _get_company_id(request)
    if not company_id:
        return False

    try:
        return UserCompanyRole.objects.filter(
            user_company__user=request.user,
            user_company__company_id=int(company_id),
            user_company__is_active=True,
            user_company__is_deleted=False,
            role__role__iexact__in=[r.lower() for r in role_names],
            role__is_deleted=False,
            is_deleted=False,
        ).exists()
    except (ValueError, TypeError):
        logger.warning(
            "Recruitment permission check: invalid company_id=%r for user=%s",
            company_id,
            getattr(request.user, "pk", "?"),
        )
        return False
    except Exception:
        logger.exception("Recruitment permission check: unexpected error")
        return False


def _has_any_role(request, role_names):
    """Check membership in any of the given roles (case-insensitive)."""
    if not request.user or not request.user.is_authenticated:
        return False

    company_id = _get_company_id(request)
    if not company_id:
        return False

    try:
        return UserCompanyRole.objects.filter(
            user_company__user=request.user,
            user_company__company_id=int(company_id),
            user_company__is_active=True,
            user_company__is_deleted=False,
            role__is_deleted=False,
            is_deleted=False,
        ).filter(
            role__role__in=[r.lower() for r in role_names]
        ).exists()
    except (ValueError, TypeError):
        return False
    except Exception:
        logger.exception("Recruitment permission check: unexpected error")
        return False


# ── Permission classes ─────────────────────────────────────────────────────────


class IsRecruitmentViewer(BasePermission):
    """
    Read-only access to recruitment data.
    Allowed roles: hr_employee, hr_manager, admin, direct_manager, employee
    """
    message = "You do not have permission to view recruitment data."
    _ALLOWED = ["hr_employee", "hr_manager", "admin", "direct_manager", "employee"]

    def has_permission(self, request, view):
        return _has_any_role(request, self._ALLOWED)


class IsHROrAdmin(BasePermission):
    """
    Write access to recruitment data (create/update/delete).
    Allowed roles: hr_employee, hr_manager, admin
    """
    message = "Only HR staff or admins can perform this action."
    _ALLOWED = ["hr_employee", "hr_manager", "admin"]

    def has_permission(self, request, view):
        return _has_any_role(request, self._ALLOWED)


class CanApproveHiringRequest(BasePermission):
    """
    Approve/reject hiring requests.
    Allowed roles: hr_employee, hr_manager, direct_manager, admin
    """
    message = "You do not have permission to approve or reject hiring requests."
    _ALLOWED = ["hr_employee", "hr_manager", "direct_manager", "admin"]

    def has_permission(self, request, view):
        return _has_any_role(request, self._ALLOWED)


class CanManageJobAdvertisements(BasePermission):
    """
    Publish/close/reopen job advertisements.
    Allowed roles: hr_employee, hr_manager, admin
    """
    message = "Only HR staff or admins can manage job advertisements."
    _ALLOWED = ["hr_employee", "hr_manager", "admin"]

    def has_permission(self, request, view):
        return _has_any_role(request, self._ALLOWED)


class CanManageCandidates(BasePermission):
    """
    Create/update/delete candidates and applications.
    Allowed roles: hr_employee, hr_manager, admin
    """
    message = "Only HR staff or admins can manage candidates."
    _ALLOWED = ["hr_employee", "hr_manager", "admin"]

    def has_permission(self, request, view):
        return _has_any_role(request, self._ALLOWED)


class CanManageInterviews(BasePermission):
    """
    Schedule interviews and record results.
    Allowed roles: hr_employee, hr_manager, direct_manager, admin
    """
    message = "You do not have permission to manage interviews."
    _ALLOWED = ["hr_employee", "hr_manager", "direct_manager", "admin"]

    def has_permission(self, request, view):
        return _has_any_role(request, self._ALLOWED)


class CanManageOffers(BasePermission):
    """
    Create/accept/decline job offers.
    Allowed roles: hr_manager, admin
    """
    message = "Only HR managers or admins can manage job offers."
    _ALLOWED = ["hr_manager", "admin"]

    def has_permission(self, request, view):
        return _has_any_role(request, self._ALLOWED)


class CanManagePostProbation(BasePermission):
    """
    Create and progress post-probation evaluations.
    Allowed roles: hr_employee, hr_manager, direct_manager, admin
    """
    message = "You do not have permission to manage post-probation evaluations."
    _ALLOWED = ["hr_employee", "hr_manager", "direct_manager", "admin"]

    def has_permission(self, request, view):
        return _has_any_role(request, self._ALLOWED)
