"""
Management command: seed demo users, company memberships, and role assignments.

Usage:
    python manage.py seed_users
    python manage.py seed_users --company-id 1
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.access_control.models import Role, UserCompany, UserCompanyRole
from apps.company.models import Company

User = get_user_model()

# ── Demo users ────────────────────────────────────────────────────────────────
# Format: (username, email, full_name, mobile, password, role_name, is_staff)

SEED_USERS = [
    {
        "username":   "hr.manager",
        "email":      "hr.manager@ouvira.dev",
        "full_name":  "Hassan Manager",
        "mobile":     "+966500000001",
        "password":   "HrManager@2026!",
        "role":       "hr_manager",
        "is_staff":   True,
    },
    {
        "username":   "hr.recruiter",
        "email":      "hr.recruiter@ouvira.dev",
        "full_name":  "Sara Recruiter",
        "mobile":     "+966500000002",
        "password":   "HrRecruiter@2026!",
        "role":       "hr_recruiter",
        "is_staff":   False,
    },
    {
        "username":   "hr.leave",
        "email":      "hr.leave@ouvira.dev",
        "full_name":  "Ahmed Leave",
        "mobile":     "+966500000003",
        "password":   "HrLeave@2026!",
        "role":       "hr_leave_manager",
        "is_staff":   False,
    },
    {
        "username":   "employee.one",
        "email":      "employee.one@ouvira.dev",
        "full_name":  "Ali Employee",
        "mobile":     "+966500000004",
        "password":   "Employee@2026!",
        "role":       "hr_employee",
        "is_staff":   False,
    },
    {
        "username":   "employee.two",
        "email":      "employee.two@ouvira.dev",
        "full_name":  "Fatima Employee",
        "mobile":     "+966500000005",
        "password":   "Employee@2026!",
        "role":       "hr_employee",
        "is_staff":   False,
    },
    {
        "username":   "hr.viewer",
        "email":      "hr.viewer@ouvira.dev",
        "full_name":  "Omar Viewer",
        "mobile":     "+966500000006",
        "password":   "HrViewer@2026!",
        "role":       "hr_viewer",
        "is_staff":   False,
    },
]


class Command(BaseCommand):
    help = "Seed demo users with company memberships and role assignments"

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
            self.stderr.write(self.style.ERROR("No company found. Run seed_roles first."))
            return

        self.stdout.write(f"\nCompany: {self.style.SUCCESS(company.name)}\n")

        for data in SEED_USERS:
            # 1. Create or get user
            user, user_created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email":          data["email"],
                    "full_name":      data["full_name"],
                    "primary_mobile": data["mobile"],
                    "is_staff":       data["is_staff"],
                    "is_active":      True,
                    "email_verified": True,
                    "phone_verified": True,
                },
            )
            if user_created:
                user.set_password(data["password"])
                user.save()
                tag = self.style.SUCCESS("created")
            else:
                tag = "already exists"
            self.stdout.write(f"  User [{data['username']}] — {tag}")

            # 2. Create or get UserCompany membership
            uc, uc_created = UserCompany.objects.get_or_create(
                user=user,
                company=company,
                defaults={"is_primary_company": True, "is_active": True},
            )
            uc_tag = self.style.SUCCESS("joined") if uc_created else "already member"
            self.stdout.write(f"    Company membership — {uc_tag}")

            # 3. Assign role
            try:
                role = Role.objects.get(company=company, role=data["role"])
                ucr, ucr_created = UserCompanyRole.objects.get_or_create(
                    user_company=uc,
                    role=role,
                )
                role_tag = self.style.SUCCESS(f"assigned [{data['role']}]") if ucr_created else f"already has [{data['role']}]"
                self.stdout.write(f"    Role — {role_tag}")
            except Role.DoesNotExist:
                self.stderr.write(
                    f"    ! Role [{data['role']}] not found — run seed_roles first"
                )

            self.stdout.write("")

        self.stdout.write(self.style.SUCCESS("Done."))
        self.stdout.write("\nCredentials summary:")
        self.stdout.write(f"  {'Username':<20} {'Password':<25} {'Role'}")
        self.stdout.write(f"  {'-'*65}")
        for d in SEED_USERS:
            self.stdout.write(f"  {d['username']:<20} {d['password']:<25} {d['role']}")
