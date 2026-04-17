from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django_tenants.utils import get_tenant_model, schema_context

User = get_user_model()

@receiver(post_delete, sender=User)
def nullify_employee_user_id(sender, instance, **kwargs):
    """When a user is deleted, nullify user_id in all tenant schemas."""
    TenantModel = get_tenant_model()
    for tenant in TenantModel.objects.exclude(schema_name='public'):
        with schema_context(tenant.schema_name):
            from apps.hris.hris_core.models import Employee
            Employee.objects.filter(user_id=instance.pk).update(user_id=None)