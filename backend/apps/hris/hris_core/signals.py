"""
hris_core signals
=================
1. Nullify employee.user_id when the auth user is deleted (cross-tenant).
2. Write an ActivityLog entry on every Employee create / update / delete.
"""
import logging
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django_tenants.utils import get_tenant_model, schema_context

logger = logging.getLogger(__name__)
User = get_user_model()


# ── 1. Nullify user_id on auth-user deletion ──────────────────────────────────

@receiver(post_delete, sender=User)
def nullify_employee_user_id(sender, instance, **kwargs):
    """When a user is deleted, nullify user_id in all tenant schemas."""
    TenantModel = get_tenant_model()
    for tenant in TenantModel.objects.exclude(schema_name="public"):
        with schema_context(tenant.schema_name):
            from apps.hris.hris_core.models import Employee
            Employee.objects.filter(user_id=instance.pk).update(user_id=None)


# ── 2. Employee audit logging ─────────────────────────────────────────────────

# Fields we want to capture in old/new value diffs
_TRACKED_FIELDS = [
    "first_name", "last_name", "national_id", "nationality",
    "gender", "marital_status", "contact_number", "secondary_phone",
    "personal_email", "address", "department_id", "location_id",
    "reporting_manager_id", "employment_type", "is_system_user",
    "national_id_status", "iqama_status", "visa_number", "fingerprint_id",
]


def _snapshot(employee) -> dict:
    """Return a dict of tracked field values for an Employee instance."""
    return {
        field: getattr(employee, field, None)
        for field in _TRACKED_FIELDS
    }


def _get_request():
    """
    Attempt to retrieve the current HTTP request from the thread-local
    store set by AuditMiddleware (if present). Returns None otherwise.
    """
    try:
        from apps.hris.hris_core.middleware import get_current_request
        return get_current_request()
    except ImportError:
        return None


def _log_employee_activity(employee, action: str, old_values: dict = None, new_values: dict = None):
    """
    Write an ActivityLog row for an Employee change.
    Requires company context — skipped silently if company is not set.
    """
    if not employee.company_id:
        return

    try:
        from django.utils import timezone
        from apps.audit.utils import get_or_create_date_dim
        from apps.audit.services import ActivityLogService

        request = _get_request()
        user = getattr(request, "user", None) if request else None
        ip = None
        if request:
            x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
            ip = x_forwarded.split(",")[0] if x_forwarded else request.META.get("REMOTE_ADDR")

        date_dim = get_or_create_date_dim(timezone.now().date())

        ActivityLogService.log_activity(
            user=user if (user and user.is_authenticated) else None,
            company_id=employee.company_id,
            date_dim=date_dim,
            entity_type="Employee",
            entity_id=employee.pk,
            action=action,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip,
        )
    except Exception:
        # Audit logging must never break the main transaction
        logger.exception(
            "Failed to write ActivityLog for Employee pk=%s action=%s",
            employee.pk,
            action,
        )


@receiver(pre_save, sender="hris_core.Employee")
def capture_employee_pre_save(sender, instance, **kwargs):
    """
    Store the pre-save snapshot on the instance so post_save can diff it.
    """
    if instance.pk:
        try:
            from apps.hris.hris_core.models import Employee
            old = Employee.objects.get(pk=instance.pk)
            instance._pre_save_snapshot = _snapshot(old)
        except sender.DoesNotExist:
            instance._pre_save_snapshot = None
    else:
        instance._pre_save_snapshot = None


@receiver(post_save, sender="hris_core.Employee")
def log_employee_save(sender, instance, created, **kwargs):
    """Log CREATE or UPDATE for an Employee."""
    if created:
        _log_employee_activity(
            employee=instance,
            action="created",
            old_values=None,
            new_values=_snapshot(instance),
        )
    else:
        old = getattr(instance, "_pre_save_snapshot", None)
        new = _snapshot(instance)
        # Only log if something actually changed
        if old and old != new:
            changed_fields = {k: v for k, v in new.items() if old.get(k) != v}
            _log_employee_activity(
                employee=instance,
                action="updated",
                old_values={k: old[k] for k in changed_fields},
                new_values=changed_fields,
            )


@receiver(post_delete, sender="hris_core.Employee")
def log_employee_delete(sender, instance, **kwargs):
    """Log hard-DELETE for an Employee (soft-delete is caught by post_save)."""
    _log_employee_activity(
        employee=instance,
        action="deleted",
        old_values=_snapshot(instance),
        new_values=None,
    )
