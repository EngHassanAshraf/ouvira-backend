"""
Management command: seed all HRIS roles, permissions, and role-permission mappings.

Usage:
    python manage.py seed_roles
    python manage.py seed_roles --company-id 1
"""
from django.core.management.base import BaseCommand
from apps.access_control.models import Role, Permission, RolePermission
from apps.company.models import Company


# ── All HRIS permissions (consolidated from all migrations) ───────────────────

ALL_PERMISSIONS = [
    # Employee
    ("employee.view",           "hris_employees",  "View employee list and profiles"),
    ("employee.create",         "hris_employees",  "Create new employees"),
    ("employee.update",         "hris_employees",  "Edit employee profiles"),
    ("employee.archive",        "hris_employees",  "Archive employees"),
    ("employee.restore",        "hris_employees",  "Restore archived employees"),
    ("employee.bulk_archive",   "hris_employees",  "Bulk archive employees"),
    ("employee.bulk_restore",   "hris_employees",  "Bulk restore employees"),
    ("employee.import",         "hris_employees",  "Import employees from Excel"),
    ("employee.export",         "hris_employees",  "Export employees to CSV"),
    # Leave
    ("leave.view_all",          "hris_leave",      "View all leave requests"),
    ("leave.create_request",    "hris_leave",      "Submit a leave request"),
    ("leave.edit_request",      "hris_leave",      "Edit own pending leave request"),
    ("leave.cancel_request",    "hris_leave",      "Cancel own leave request"),
    ("leave.approve_request",   "hris_leave",      "Approve leave requests"),
    ("leave.reject_request",    "hris_leave",      "Reject leave requests"),
    ("leave.manage_types",      "hris_leave",      "Create/edit/delete leave types"),
    ("leave.edit_balance",      "hris_leave",      "Adjust employee leave balances"),
    # Travel
    ("travel.view_all",         "hris_travel",     "View all travel requests"),
    ("travel.create_request",   "hris_travel",     "Submit a travel request"),
    ("travel.edit_request",     "hris_travel",     "Edit own travel request"),
    ("travel.cancel_request",   "hris_travel",     "Cancel own travel request"),
    # Attendance
    ("attendance.view",         "hris_attendance", "View attendance records"),
    ("attendance.manage",       "hris_attendance", "Create/edit attendance records"),
    # Audit
    ("audit.view_logs",         "hris_audit",      "View employee activity logs"),
    # Recruitment — Hiring Request
    ("hris_recruitment.view_hiring_request",    "hris_recruitment", "View hiring requests"),
    ("hris_recruitment.create_hiring_request",  "hris_recruitment", "Create hiring requests"),
    ("hris_recruitment.update_hiring_request",  "hris_recruitment", "Update hiring requests"),
    ("hris_recruitment.delete_hiring_request",  "hris_recruitment", "Delete hiring requests"),
    ("hris_recruitment.approve_hiring_request", "hris_recruitment", "Approve hiring requests"),
    ("hris_recruitment.reject_hiring_request",  "hris_recruitment", "Reject hiring requests"),
    # Recruitment — Job Advertisement
    ("hris_recruitment.view_job_advertisement",    "hris_recruitment", "View job advertisements"),
    ("hris_recruitment.create_job_advertisement",  "hris_recruitment", "Create job advertisements"),
    ("hris_recruitment.update_job_advertisement",  "hris_recruitment", "Update job advertisements"),
    ("hris_recruitment.delete_job_advertisement",  "hris_recruitment", "Delete job advertisements"),
    ("hris_recruitment.publish_job_advertisement", "hris_recruitment", "Publish job advertisements"),
    ("hris_recruitment.close_job_advertisement",   "hris_recruitment", "Close job advertisements"),
    # Recruitment — Candidate
    ("hris_recruitment.view_candidate",       "hris_recruitment", "View candidates"),
    ("hris_recruitment.create_candidate",     "hris_recruitment", "Create candidates"),
    ("hris_recruitment.update_candidate",     "hris_recruitment", "Update candidates"),
    ("hris_recruitment.delete_candidate",     "hris_recruitment", "Delete candidates"),
    ("hris_recruitment.view_job_application", "hris_recruitment", "View job applications"),
    ("hris_recruitment.move_to_stage",        "hris_recruitment", "Move application stage"),
    ("hris_recruitment.delete_job_application","hris_recruitment", "Delete job applications"),
    # Recruitment — Interview
    ("hris_recruitment.view_interview",            "hris_recruitment", "View interviews"),
    ("hris_recruitment.create_interview",          "hris_recruitment", "Schedule interviews"),
    ("hris_recruitment.update_interview",          "hris_recruitment", "Update interviews"),
    ("hris_recruitment.delete_interview",          "hris_recruitment", "Delete interviews"),
    ("hris_recruitment.record_interview_result",   "hris_recruitment", "Record interview results"),
    ("hris_recruitment.view_candidate_document",   "hris_recruitment", "View candidate documents"),
    ("hris_recruitment.verify_candidate_document", "hris_recruitment", "Verify candidate documents"),
    # Recruitment — Finalization
    ("hris_recruitment.view_job_offer",    "hris_recruitment", "View job offers"),
    ("hris_recruitment.create_job_offer",  "hris_recruitment", "Create job offers"),
    ("hris_recruitment.update_job_offer",  "hris_recruitment", "Update job offers"),
    ("hris_recruitment.delete_job_offer",  "hris_recruitment", "Delete job offers"),
    ("hris_recruitment.accept_job_offer",  "hris_recruitment", "Accept job offers"),
    ("hris_recruitment.view_onboarding",   "hris_recruitment", "View onboarding"),
    ("hris_recruitment.update_onboarding", "hris_recruitment", "Update onboarding tasks"),
]


# ── Role definitions ──────────────────────────────────────────────────────────

ROLES = {
    # Full access to all HRIS modules
    "hr_manager": {
        "desc": "HR Manager — full HRIS access",
        "permissions": [p[0] for p in ALL_PERMISSIONS],
    },

    # Recruitment specialist — full recruitment + limited employee/leave
    "hr_recruiter": {
        "desc": "HR Recruiter — full recruitment pipeline access",
        "permissions": [
            "employee.view",
            "hris_recruitment.view_hiring_request",
            "hris_recruitment.create_hiring_request",
            "hris_recruitment.update_hiring_request",
            "hris_recruitment.approve_hiring_request",
            "hris_recruitment.reject_hiring_request",
            "hris_recruitment.view_job_advertisement",
            "hris_recruitment.create_job_advertisement",
            "hris_recruitment.update_job_advertisement",
            "hris_recruitment.publish_job_advertisement",
            "hris_recruitment.close_job_advertisement",
            "hris_recruitment.view_candidate",
            "hris_recruitment.create_candidate",
            "hris_recruitment.update_candidate",
            "hris_recruitment.view_job_application",
            "hris_recruitment.move_to_stage",
            "hris_recruitment.view_interview",
            "hris_recruitment.create_interview",
            "hris_recruitment.update_interview",
            "hris_recruitment.record_interview_result",
            "hris_recruitment.view_candidate_document",
            "hris_recruitment.verify_candidate_document",
            "hris_recruitment.view_job_offer",
            "hris_recruitment.create_job_offer",
            "hris_recruitment.update_job_offer",
            "hris_recruitment.accept_job_offer",
            "hris_recruitment.view_onboarding",
            "hris_recruitment.update_onboarding",
        ],
    },

    # Leave manager — manages leave for the team
    "hr_leave_manager": {
        "desc": "Leave Manager — manages team leave",
        "permissions": [
            "employee.view",
            "leave.view_all",
            "leave.approve_request",
            "leave.reject_request",
            "leave.manage_types",
            "leave.edit_balance",
            "attendance.view",
            "attendance.manage",
        ],
    },

    # Regular employee — self-service only
    "hr_employee": {
        "desc": "HR Employee — self-service access",
        "permissions": [
            "employee.view",
            "leave.create_request",
            "leave.edit_request",
            "leave.cancel_request",
            "travel.create_request",
            "travel.edit_request",
            "travel.cancel_request",
            "attendance.view",
        ],
    },

    # Read-only viewer
    "hr_viewer": {
        "desc": "HR Viewer — read-only access",
        "permissions": [
            "employee.view",
            "leave.view_all",
            "travel.view_all",
            "attendance.view",
            "hris_recruitment.view_hiring_request",
            "hris_recruitment.view_job_advertisement",
            "hris_recruitment.view_candidate",
            "hris_recruitment.view_job_application",
            "hris_recruitment.view_interview",
            "hris_recruitment.view_job_offer",
            "hris_recruitment.view_onboarding",
        ],
    },
}


class Command(BaseCommand):
    help = "Seed all HRIS roles and permissions for a company"

    def add_arguments(self, parser):
        parser.add_argument(
            "--company-id",
            type=int,
            default=None,
            help="Company ID (defaults to first company)",
        )

    def handle(self, *args, **options):
        company_id = options.get("company_id")
        company = (
            Company.objects.get(pk=company_id)
            if company_id
            else Company.objects.first()
        )

        if not company:
            self.stderr.write(self.style.ERROR("No company found."))
            return

        self.stdout.write(f"\nCompany: {self.style.SUCCESS(company.name)}\n")

        # 1. Ensure all permissions exist
        self.stdout.write("── Syncing permissions ──")
        perm_created = 0
        for code, module, description in ALL_PERMISSIONS:
            _, created = Permission.objects.get_or_create(
                code=code,
                defaults={"module": module, "description": description},
            )
            if created:
                self.stdout.write(f"  + {code}")
                perm_created += 1
        self.stdout.write(f"  {perm_created} new permissions created\n")

        # 2. Create roles and assign permissions
        self.stdout.write("── Seeding roles ──")
        for role_name, config in ROLES.items():
            role, role_created = Role.objects.get_or_create(
                company=company,
                role=role_name,
                defaults={"is_system_role": True, "desc": config["desc"]},
            )
            tag = self.style.SUCCESS("created") if role_created else "exists"
            self.stdout.write(f"\n  [{role_name}] — {tag}")

            rp_created = 0
            for code in config["permissions"]:
                try:
                    perm = Permission.objects.get(code=code)
                    _, created = RolePermission.objects.get_or_create(
                        role=role, permission=perm, defaults={"granted": True}
                    )
                    if created:
                        rp_created += 1
                except Permission.DoesNotExist:
                    self.stderr.write(f"    ! Missing permission: {code}")

            self.stdout.write(f"    {rp_created} new permissions assigned")

        self.stdout.write(f"\n{self.style.SUCCESS('Done.')}")
