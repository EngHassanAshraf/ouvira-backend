from django.db import migrations

def seed_permissions(apps, schema_editor):
    Permission = apps.get_model('access_control', 'Permission')
    
    permissions = [
        ('hris_recruitment.view_hiring_request', 'Recruitment', 'Can view hiring requests'),
        ('hris_recruitment.create_hiring_request', 'Recruitment', 'Can create hiring requests'),
        ('hris_recruitment.update_hiring_request', 'Recruitment', 'Can update hiring requests'),
        ('hris_recruitment.delete_hiring_request', 'Recruitment', 'Can delete hiring requests'),
        ('hris_recruitment.approve_hiring_request', 'Recruitment', 'Can approve hiring requests'),
        ('hris_recruitment.reject_hiring_request', 'Recruitment', 'Can reject hiring requests'),
    ]
    
    for code, module, description in permissions:
        Permission.objects.get_or_create(
            code=code,
            defaults={
                'module': module,
                'description': description
            }
        )

def remove_permissions(apps, schema_editor):
    Permission = apps.get_model('access_control', 'Permission')
    codes = [
        'hris_recruitment.view_hiring_request',
        'hris_recruitment.create_hiring_request',
        'hris_recruitment.update_hiring_request',
        'hris_recruitment.delete_hiring_request',
        'hris_recruitment.approve_hiring_request',
        'hris_recruitment.reject_hiring_request',
    ]
    Permission.objects.filter(code__in=codes).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('hris_recruitment', '0002_hiringrequest_hiringrequestapproval'),
        ('access_control', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_permissions, remove_permissions),
    ]
