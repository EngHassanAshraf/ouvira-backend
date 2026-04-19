import os
import django
from django_tenants.utils import schema_context

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

def setup_data():
    schema_name = 'shawahid'
    with schema_context('public'):
        from apps.tenant.models import Tenant
        tenant = Tenant.objects.get(schema_name=schema_name)
        tenant_id = tenant.id

    with schema_context(schema_name):
        from apps.company.models import Company
        from apps.hris.hris_core.models.organization import Department, JobTitle
        from apps.access_control.models import Role, UserCompany, UserCompanyRole
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            root = User.objects.get(username='root')
        except User.DoesNotExist:
            with schema_context('public'):
                root = User.objects.get(username='root')

        # Handle existing company with same name but wrong ID
        existing = Company.objects.filter(name='Shawahid Test Co').first()
        if existing and existing.id != tenant_id:
            print(f"Deleting existing company with wrong ID ({existing.id})")
            existing.delete()

        # Create Company with ID matching Tenant ID
        company, _ = Company.objects.get_or_create(
            id=tenant_id,
            defaults={
                'name': 'Shawahid Test Co', 
                'create_by_id': 1, 
                'address': 'Test Address'
            }
        )

        # Link user
        import os
        dev_password = os.getenv("DEV_SEED_PASSWORD", "changeme")
        dev_mobile = os.getenv("DEV_SEED_MOBILE", "+10000000000")
        user, created = User.objects.get_or_create(
            username="root",
            defaults={"full_name": "Root Admin", "primary_mobile": dev_mobile, "is_staff": True, "is_active": True}
        )
        user.set_password(dev_password)
        user.is_active = True
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save()
        print(f"USER_READY: {user.username}")

        user_company, _ = UserCompany.objects.get_or_create(
            user=user,
            company=company,
            defaults={'is_primary_company': True, 'is_active': True}
        )

        # Ensure role is 'Admin' to satisfy IsAdminUser permission
        admin_role, _ = Role.objects.get_or_create(
            company=company, 
            role='Admin', 
            defaults={'is_system_role': True}
        )
        # Fix: UserCompanyRole does not have is_active field
        UserCompanyRole.objects.get_or_create(
            user_company=user_company, 
            role=admin_role
        )

        # Create Dept & Title
        Department.objects.get_or_create(name='Engineering', company=company)
        JobTitle.objects.get_or_create(title='Software Engineer', company=company)

        print(f"SETUP_SUCCESS: Role=Admin, CompanyID={company.id}")

if __name__ == "__main__":
    setup_data()
