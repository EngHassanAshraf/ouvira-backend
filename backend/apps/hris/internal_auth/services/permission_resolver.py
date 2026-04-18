"""
PermissionResolver
==================
Aggregates effective permissions for a user in a specific company context.

Flow:
  1. Fetch all active UserCompanyRole rows for (user, company)
  2. For each role, fetch granted RolePermission rows
  3. Flatten + deduplicate permission codes
  4. Cache result in Redis (TTL = 5 min, keyed by user+company)
  5. Return sorted list of permission codes

Cache invalidation:
  Call PermissionResolver.invalidate(user_id, company_id) whenever roles or
  permissions change for this user/company pair.

Module access:
  Derived from permission namespaces (e.g. "hr.view_employee" → module "hr").
  Returned as a sorted deduplicated list of module names.
"""
import logging
from typing import Optional

from django.core.cache import cache

from apps.access_control.models import UserCompanyRole, RolePermission

logger = logging.getLogger(__name__)

# Cache TTL in seconds — short enough to pick up role changes quickly
_CACHE_TTL = 300  # 5 minutes
_CACHE_KEY = "internal_auth:perms:{user_id}:{company_id}"


class PermissionResolver:

    @staticmethod
    def _cache_key(user_id: int, company_id: int) -> str:
        return _CACHE_KEY.format(user_id=user_id, company_id=company_id)

    @staticmethod
    def resolve(user_id: int, company_id: int) -> dict:
        """
        Return effective permissions and module access for a user in a company.

        Returns:
            {
                "permissions": ["hr.view_employee", "hr.edit_employee", ...],
                "modules": ["hr", "payroll", ...],
                "roles": ["HR_ADMIN", "PAYROLL_VIEWER", ...],
            }
        """
        cache_key = PermissionResolver._cache_key(user_id, company_id)
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(
                "PermissionResolver cache hit | user_id=%s company_id=%s",
                user_id, company_id,
            )
            return cached

        result = PermissionResolver._compute(user_id, company_id)
        cache.set(cache_key, result, timeout=_CACHE_TTL)
        logger.debug(
            "PermissionResolver computed | user_id=%s company_id=%s perms=%d",
            user_id, company_id, len(result["permissions"]),
        )
        return result

    @staticmethod
    def _compute(user_id: int, company_id: int) -> dict:
        # 1. All active role assignments for this user+company
        ucr_qs = (
            UserCompanyRole.objects.filter(
                user_company__user_id=user_id,
                user_company__company_id=company_id,
                user_company__is_active=True,
                user_company__is_deleted=False,
                role__is_deleted=False,
                is_deleted=False,
            )
            .select_related("role")
        )

        role_ids = []
        role_names = []
        for ucr in ucr_qs:
            role_ids.append(ucr.role_id)
            role_names.append(ucr.role.role)

        if not role_ids:
            return {"permissions": [], "modules": [], "roles": []}

        # 2. All granted permissions for those roles
        perm_qs = (
            RolePermission.objects.filter(
                role_id__in=role_ids,
                granted=True,
                is_deleted=False,
                permission__is_deleted=False,
            )
            .select_related("permission")
            .values_list("permission__code", "permission__module")
        )

        perm_codes = sorted(set(code for code, _ in perm_qs))
        modules = sorted(set(mod.lower() for _, mod in perm_qs if mod))

        return {
            "permissions": perm_codes,
            "modules": modules,
            "roles": sorted(set(role_names)),
        }

    @staticmethod
    def invalidate(user_id: int, company_id: int) -> None:
        """Evict cached permissions for a user+company pair."""
        cache.delete(PermissionResolver._cache_key(user_id, company_id))
        logger.info(
            "PermissionResolver cache invalidated | user_id=%s company_id=%s",
            user_id, company_id,
        )
