"""
Management command: seed hr_manager and hr_employee roles with permissions.

Usage:
    python manage.py seed_roles
    python manage.py seed_roles --company-id 1
"""
from django.core.management.base import BaseCommand
from apps.access_control.models import Role, Permission, RolePermission
from apps.company.models import Company


HR_MANAGER_PERMS = [
    "employee.view", "employee.create", "employee.update",
    "employee.archive", "employee.restore",
    "employee.bulk_archive", "employee.bulk_restore",
    "employee.import", "employee.export",
    "leave.view_all", "leave.approve_request", "leave.reject_request",
    "leave.manage_types", "leave.edit_balance",
    "travel.view_all",
    "attendance.view", "attendance.manage",
    "audit.view_logs",
]

HR_EMPLOYEE_PERMS = [
    "employee.view",
    "leave.create_request", "leave.edit_request", "leave.cancel_request",
    "travel.create_request", "travel.edit_request", "travel.cancel_request",
    "attendance.view",
]

ROLES = {
    "hr_manager": HR_MANAGER_PERMS,
    "hr_employee": HR_EMPLOYEE_PERMS,
}


class Command(BaseCommand):
    help = "Seed hr_manager and hr_employee roles with HRIS permissions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--company-id",
            type=int,
            default=None,
            help="Company ID to seed roles for (defaults to first company)",
        )

    def handle(self, *args, **options):
        company_id = options.get("company_id")
        if company_id:
            company = Company.objects.get(pk=company_id)
        else:
            company = Company.objects.first()

        if not company:
            self.stderr.write("ERROR: No company found.")
            return

        self.stdout.write(f"Seeding roles for company: {company.name}")

        for role_name, perm_codes in ROLES.items():
            role, created = Role.objects.get_or_create(
                company=company,
                role=role_name,
                defaults={"is_system_role": True, "desc": f"System role: {role_name}"},
            )
            status = self.style.SUCCESS("created") if created else "already exists"
            self.stdout.write(f"  Role [{role_name}] — {status}")

            for code in perm_codes:
                try:
                    perm = Permission.objects.get(code=code)
                    _, rp_created = RolePermission.objects.get_or_create(
                        role=role, permission=perm, defaults={"granted": True}
                    )
                    if rp_created:
                        self.stdout.write(f"    + {code}")
                except Permission.DoesNotExist:
                    self.stderr.write(f"    ! Permission not found: {code}")

        self.stdout.write(self.style.SUCCESS("Done."))
