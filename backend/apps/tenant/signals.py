"""
Tenant signals — auto-create a Company record whenever a new tenant schema
is provisioned via `create_tenant` (or any other path that saves a Tenant).

django-tenants fires `post_schema_sync` after the schema is created and all
tenant migrations have run.  We listen to that signal so the Company row is
written inside the *tenant* schema (connection is already switched by then).

If `post_schema_sync` is not available (older django-tenants builds), we fall
back to a plain `post_save` on Tenant — which fires in the *public* schema,
so the Company ends up in the public schema.  That fallback is kept only for
safety; the primary path is `post_schema_sync`.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

# ── Primary: post_schema_sync (django-tenants ≥ 3.x) ─────────────────────────
try:
    from django_tenants.signals import post_schema_sync

    @receiver(post_schema_sync)
    def create_company_on_schema_sync(sender, tenant, **kwargs):
        """
        Called after django-tenants has created the tenant schema and run all
        tenant-level migrations.  The DB connection is already pointing at the
        new tenant schema, so Company.objects.create() writes there.
        """
        _provision_company(tenant)

    _using_schema_sync = True

except ImportError:
    _using_schema_sync = False
    logger.warning(
        "django_tenants.signals.post_schema_sync not found — "
        "falling back to post_save on Tenant."
    )


# ── Fallback: post_save on Tenant ─────────────────────────────────────────────
if not _using_schema_sync:
    from apps.tenant.models import Tenant

    @receiver(post_save, sender=Tenant)
    def create_company_on_tenant_save(sender, instance, created, **kwargs):
        if created:
            _provision_company(instance)


# ── Shared helper ─────────────────────────────────────────────────────────────

def _provision_company(tenant) -> None:
    """
    Create a Company (and default CompanySettings) for *tenant*.

    `create_by` is intentionally left NULL — the tenant is created by a
    management command that has no authenticated user context.  The field is
    already nullable in the Company model.
    """
    try:
        from apps.company.models import Company, CompanySettings

        if Company.objects.filter(name=tenant.name).exists():
            logger.info(
                "Company '%s' already exists for tenant — skipping creation.",
                tenant.name,
            )
            return

        company = Company.objects.create(
            name=tenant.name,
            status=Company.Status.ACTIVE,
            create_by=None,  # no user context in management commands
        )

        # Bootstrap default settings so the tenant is immediately usable
        CompanySettings.objects.get_or_create(
            company=company,
            defaults={
                "default_language": "en",
                "default_currency": "USD",
                "timezone": "UTC",
                "fiscal_year_start_month": 1,
                "feature_flags": {},
            },
        )

        logger.info(
            "Auto-created Company '%s' (id=%s) for tenant schema '%s'.",
            company.name,
            company.pk,
            tenant.schema_name,
        )

    except Exception as exc:  # pragma: no cover
        # Never let a signal crash the tenant-creation flow
        logger.exception(
            "Failed to auto-create Company for tenant '%s': %s",
            getattr(tenant, "name", "?"),
            exc,
        )
