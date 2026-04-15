"""
RedirectResolver
================
Maps a user's primary role to a default module + frontend route.

Covers ALL ERP modules:
  - Admin / Super Admin
  - HR (employees, recruitment, leave, attendance, onboarding, performance)
  - Payroll
  - Finance / Accounting
  - Inventory / Warehouse
  - Procurement / Purchasing
  - Sales / CRM
  - Projects / PMO
  - IT / Support
  - Legal / Compliance
  - Marketing
  - Operations
  - Self-Service (default employee portal)

Priority order: highest privilege wins.
Add new roles by inserting into ROLE_REDIRECT_MAP and _PRIORITY.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ── Role → (module_key, frontend_path) ────────────────────────────────────────
# Keys are lowercase. Values: (module, path).
# module is the machine-readable module identifier returned to the frontend.
# path  is the default landing route for that role.

ROLE_REDIRECT_MAP: dict[str, tuple[str, str]] = {

    # ── Platform administration ────────────────────────────────────────────────
    "super_admin":                  ("admin",        "/admin/dashboard"),
    "admin":                        ("admin",        "/admin/dashboard"),
    "system_admin":                 ("admin",        "/admin/dashboard"),

    # ── HR ────────────────────────────────────────────────────────────────────
    "hr_admin":                     ("hr",           "/hr/dashboard"),
    "hr_manager":                   ("hr",           "/hr/dashboard"),
    "hr_employee":                  ("hr",           "/hr/employees"),
    "hr_staff":                     ("hr",           "/hr/employees"),
    "recruitment_manager":          ("recruitment",  "/recruitment/dashboard"),
    "recruiter":                    ("recruitment",  "/recruitment/pipeline"),
    "leave_manager":                ("hr",           "/hr/leave/requests"),
    "attendance_manager":           ("hr",           "/hr/attendance"),
    "performance_manager":          ("hr",           "/hr/performance"),
    "training_manager":             ("hr",           "/hr/training"),
    "onboarding_manager":           ("hr",           "/hr/onboarding"),

    # ── Payroll ───────────────────────────────────────────────────────────────
    "payroll_admin":                ("payroll",      "/payroll/dashboard"),
    "payroll_manager":              ("payroll",      "/payroll/overview"),
    "payroll_staff":                ("payroll",      "/payroll/runs"),
    "compensation_manager":         ("payroll",      "/payroll/compensation"),
    "benefits_manager":             ("payroll",      "/payroll/benefits"),

    # ── Finance / Accounting ──────────────────────────────────────────────────
    "finance_director":             ("finance",      "/finance/dashboard"),
    "finance_manager":              ("finance",      "/finance/dashboard"),
    "accountant":                   ("finance",      "/finance/ledger"),
    "accounts_payable":             ("finance",      "/finance/payables"),
    "accounts_receivable":          ("finance",      "/finance/receivables"),
    "budget_manager":               ("finance",      "/finance/budgets"),
    "tax_manager":                  ("finance",      "/finance/tax"),
    "auditor":                      ("finance",      "/finance/audit"),

    # ── Inventory / Warehouse ─────────────────────────────────────────────────
    "inventory_manager":            ("inventory",    "/inventory/dashboard"),
    "warehouse_manager":            ("inventory",    "/inventory/warehouse"),
    "stock_controller":             ("inventory",    "/inventory/stock"),
    "inventory_staff":              ("inventory",    "/inventory/items"),

    # ── Procurement / Purchasing ──────────────────────────────────────────────
    "procurement_manager":          ("procurement",  "/procurement/dashboard"),
    "purchasing_manager":           ("procurement",  "/procurement/orders"),
    "purchasing_officer":           ("procurement",  "/procurement/requests"),
    "vendor_manager":               ("procurement",  "/procurement/vendors"),

    # ── Sales / CRM ───────────────────────────────────────────────────────────
    "sales_director":               ("sales",        "/sales/dashboard"),
    "sales_manager":                ("sales",        "/sales/pipeline"),
    "sales_representative":         ("sales",        "/sales/leads"),
    "account_manager":              ("sales",        "/sales/accounts"),
    "crm_admin":                    ("sales",        "/sales/dashboard"),

    # ── Projects / PMO ────────────────────────────────────────────────────────
    "pmo_director":                 ("projects",     "/projects/dashboard"),
    "project_manager":              ("projects",     "/projects/my-projects"),
    "project_coordinator":          ("projects",     "/projects/tasks"),
    "project_member":               ("projects",     "/projects/tasks"),

    # ── IT / Support ──────────────────────────────────────────────────────────
    "it_manager":                   ("it",           "/it/dashboard"),
    "it_admin":                     ("it",           "/it/assets"),
    "it_support":                   ("it",           "/it/tickets"),
    "helpdesk_agent":               ("it",           "/it/tickets"),

    # ── Legal / Compliance ────────────────────────────────────────────────────
    "legal_manager":                ("legal",        "/legal/dashboard"),
    "compliance_officer":           ("legal",        "/legal/compliance"),
    "legal_counsel":                ("legal",        "/legal/contracts"),

    # ── Marketing ─────────────────────────────────────────────────────────────
    "marketing_director":           ("marketing",    "/marketing/dashboard"),
    "marketing_manager":            ("marketing",    "/marketing/campaigns"),
    "marketing_staff":              ("marketing",    "/marketing/campaigns"),

    # ── Operations ────────────────────────────────────────────────────────────
    "operations_director":          ("operations",   "/operations/dashboard"),
    "operations_manager":           ("operations",   "/operations/overview"),
    "operations_staff":             ("operations",   "/operations/tasks"),

    # ── Line management (cross-module) ────────────────────────────────────────
    "direct_manager":               ("hr",           "/hr/team"),
    "department_manager":           ("hr",           "/hr/team"),
    "manager":                      ("hr",           "/hr/team"),

    # ── Default employee self-service ─────────────────────────────────────────
    "employee":                     ("self",         "/self-service/dashboard"),
}

# ── Priority list — first match wins ──────────────────────────────────────────
# Ordered from highest privilege to lowest.
_PRIORITY: list[str] = [
    # Platform
    "super_admin", "system_admin", "admin",
    # Finance
    "finance_director",
    # HR leadership
    "hr_admin", "hr_manager",
    # Payroll leadership
    "payroll_admin", "payroll_manager",
    # Sales leadership
    "sales_director", "crm_admin",
    # Procurement leadership
    "procurement_manager",
    # Inventory leadership
    "inventory_manager", "warehouse_manager",
    # Projects leadership
    "pmo_director",
    # IT leadership
    "it_manager", "it_admin",
    # Legal leadership
    "legal_manager",
    # Marketing leadership
    "marketing_director",
    # Operations leadership
    "operations_director", "operations_manager",
    # Mid-level
    "recruitment_manager", "leave_manager", "performance_manager",
    "training_manager", "onboarding_manager", "attendance_manager",
    "compensation_manager", "benefits_manager",
    "finance_manager", "budget_manager", "tax_manager", "auditor",
    "accounts_payable", "accounts_receivable", "accountant",
    "purchasing_manager", "vendor_manager",
    "stock_controller",
    "sales_manager", "account_manager",
    "project_manager",
    "it_support", "helpdesk_agent",
    "compliance_officer", "legal_counsel",
    "marketing_manager",
    # Staff
    "hr_employee", "hr_staff",
    "payroll_staff",
    "purchasing_officer",
    "inventory_staff",
    "sales_representative",
    "project_coordinator", "project_member",
    "marketing_staff",
    "operations_staff",
    "recruiter",
    # Line management
    "department_manager", "direct_manager", "manager",
    # Default
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

        # Fallback: try first role in the list directly
        first = normalized[0]
        if first in ROLE_REDIRECT_MAP:
            module, path = ROLE_REDIRECT_MAP[first]
            return {"module": module, "path": path}

        return _DEFAULT_REDIRECT

    @staticmethod
    def get_all_modules() -> list[str]:
        """Return all distinct module keys — useful for frontend module discovery."""
        return sorted(set(module for module, _ in ROLE_REDIRECT_MAP.values()))
