"""
RedirectResolver
================
Maps a user's primary role to a default module + frontend route.

Priority order (highest first):
  1. SUPER_ADMIN / ADMIN
  2. HR_MANAGER / HR_ADMIN
  3. HR_EMPLOYEE / HR_STAFF
  4. PAYROLL_MANAGER
  5. PAYROLL_STAFF
  6. DIRECT_MANAGER / MANAGER
  7. EMPLOYEE (default)

The mapping is intentionally simple and configurable — extend
ROLE_REDIRECT_MAP to add new modules as the ERP grows.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Role name → (module, path)
# Keys are lowercase for case-insensitive matching.
ROLE_REDIRECT_MAP: dict[str, tuple[str, str]] = {
    "super_admin":       ("admin",     "/admin/dashboard"),
    "admin":             ("admin",     "/admin/dashboard"),
    "hr_admin":          ("hr",        "/hr/dashboard"),
    "hr_manager":        ("hr",        "/hr/dashboard"),
    "hr_employee":       ("hr",        "/hr/employees"),
    "hr_staff":          ("hr",        "/hr/employees"),
    "payroll_manager":   ("payroll",   "/payroll/overview"),
    "payroll_staff":     ("payroll",   "/payroll/overview"),
    "direct_manager":    ("hr",        "/hr/team"),
    "manager":           ("hr",        "/hr/team"),
    "employee":          ("self",      "/self-service/dashboard"),
}

# Priority list — first match wins
_PRIORITY: list[str] = [
    "super_admin",
    "admin",
    "hr_admin",
    "hr_manager",
    "hr_employee",
    "hr_staff",
    "payroll_manager",
    "payroll_staff",
    "direct_manager",
    "manager",
    "employee",
]

_DEFAULT_REDIRECT = {"module": "self", "path": "/self-service/dashboard"}


class RedirectResolver:

    @staticmethod
    def resolve(roles: list[str]) -> dict:
        """
        Given a list of role names, return the highest-priority redirect.

        Returns:
            {"module": "hr", "path": "/hr/dashboard"}
        """
        if not roles:
            return _DEFAULT_REDIRECT

        normalized = [r.lower() for r in roles]

        for priority_role in _PRIORITY:
            if priority_role in normalized:
                module, path = ROLE_REDIRECT_MAP[priority_role]
                logger.debug(
                    "RedirectResolver matched role=%s → module=%s path=%s",
                    priority_role, module, path,
                )
                return {"module": module, "path": path}

        # Fallback: try first role in the list
        first = normalized[0]
        if first in ROLE_REDIRECT_MAP:
            module, path = ROLE_REDIRECT_MAP[first]
            return {"module": module, "path": path}

        return _DEFAULT_REDIRECT
