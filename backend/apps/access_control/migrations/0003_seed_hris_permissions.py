"""
Seed HRIS permission codes.
These map to the permission codes used by HasModulePermission in views.
"""
from django.db import migrations

HRIS_PERMISSIONS = [
    # ── Employee management ────────────────────────────────────────────────────
    ("employee.view",           "hris_employees",  "View employee list and profiles"),
    ("employee.create",         "hris_employees",  "Create new employees"),
    ("employee.update",         "hris_employees",  "Edit employee profiles"),
    ("employee.archive",        "hris_employees",  "Archive (soft-delete) employees"),
    ("employee.restore",        "hris_employees",  "Restore archived employees"),
    ("employee.bulk_archive",   "hris_employees",  "Bulk archive employees"),
    ("employee.bulk_restore",   "hris_employees",  "Bulk restore employees"),
    ("employee.import",         "hris_employees",  "Import employees from Excel"),
    ("employee.export",         "hris_employees",  "Export employees to CSV"),
    # ── Leave management ───────────────────────────────────────────────────────
    ("leave.view_all",          "hris_leave",      "View all leave requests"),
    ("leave.create_request",    "hris_leave",      "Submit a leave request"),
    ("leave.edit_request",      "hris_leave",      "Edit own pending leave request"),
    ("leave.cancel_request",    "hris_leave",      "Cancel own leave request"),
    ("leave.approve_request",   "hris_leave",      "Approve leave requests"),
    ("leave.reject_request",    "hris_leave",      "Reject leave requests"),
    ("leave.manage_types",      "hris_leave",      "Create / edit / delete leave types"),
    ("leave.edit_balance",      "hris_leave",      "Adjust employee leave balances"),
    # ── Business trip management ───────────────────────────────────────────────
    ("travel.view_all",         "hris_travel",     "View all travel requests"),
    ("travel.create_request",   "hris_travel",     "Submit a travel request"),
    ("travel.edit_request",     "hris_travel",     "Edit own travel request"),
    ("travel.cancel_request",   "hris_travel",     "Cancel own travel request"),
    # ── Attendance ─────────────────────────────────────────────────────────────
    ("attendance.view",         "hris_attendance", "View attendance records"),
    ("attendance.manage",       "hris_attendance", "Create / edit attendance records"),
    # ── Audit log ──────────────────────────────────────────────────────────────
    ("audit.view_logs",         "hris_audit",      "View employee activity logs"),
]


def seed_permissions(apps, schema_editor):
    Permission = apps.get_model("access_control", "Permission")
    for code, module, description in HRIS_PERMISSIONS:
        Permission.objects.get_or_create(
            code=code,
            defaults={"module": module, "description": description},
        )


def unseed_permissions(apps, schema_editor):
    Permission = apps.get_model("access_control", "Permission")
    codes = [p[0] for p in HRIS_PERMISSIONS]
    Permission.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("access_control", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(seed_permissions, reverse_code=unseed_permissions),
    ]
