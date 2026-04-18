"""
Tenant signals
==============
Auto-create a Company record inside the tenant schema whenever a new Tenant
is provisioned (e.g. via `python manage.py create_tenant`).
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django_tenants.utils import schema_context

from .models import Tenant

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Tenant)
def create_company_for_new_tenant(sender, instance: Tenant, created: bool, **kwargs):
    """
    When a new Tenant row is saved (and its schema has been created),
    switch into that schema and create the default Company record.
    """
    if not created:
        return

    # Skip the public schema — it holds no tenant data
    if instance.schema_name == "public":
        return

    try:
        with schema_context(instance.schema_name):
            from apps.company.models import Company

            # Avoid duplicate creation if signal fires more than once
            if Company.objects.filter(name=instance.name).exists():
                logger.info(
                    "Company '%s' already exists in schema '%s' — skipping.",
                    instance.name,
                    instance.schema_name,
                )
                return

            company = Company.objects.create(
                name=instance.name,
                is_parent_company=True,
                create_by=None,  # system-created; no user context available
            )
            logger.info(
                "Auto-created Company '%s' (pk=%s) in schema '%s'.",
                company.name,
                company.pk,
                instance.schema_name,
            )
    except Exception:
        # Never let a signal failure break tenant provisioning
        logger.exception(
            "Failed to auto-create Company for tenant '%s' (schema='%s').",
            instance.name,
            instance.schema_name,
        )
