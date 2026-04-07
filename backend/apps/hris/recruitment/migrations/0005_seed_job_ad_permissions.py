from django.db import migrations

def seed_job_ad_permissions(apps, schema_editor):
    Permission = apps.get_model('access_control', 'Permission')
    
    permissions = [
        ('hris_recruitment.view_job_advertisement', 'Recruitment', 'Can view job advertisements'),
        ('hris_recruitment.create_job_advertisement', 'Recruitment', 'Can create job advertisements'),
        ('hris_recruitment.update_job_advertisement', 'Recruitment', 'Can update job advertisements'),
        ('hris_recruitment.delete_job_advertisement', 'Recruitment', 'Can delete job advertisements'),
        ('hris_recruitment.publish_job_advertisement', 'Recruitment', 'Can publish job advertisements'),
        ('hris_recruitment.close_job_advertisement', 'Recruitment', 'Can close job advertisements'),
    ]
    
    for code, module, description in permissions:
        Permission.objects.get_or_create(
            code=code,
            defaults={
                'module': module,
                'description': description
            }
        )

def remove_job_ad_permissions(apps, schema_editor):
    Permission = apps.get_model('access_control', 'Permission')
    codes = [
        'hris_recruitment.view_job_advertisement',
        'hris_recruitment.create_job_advertisement',
        'hris_recruitment.update_job_advertisement',
        'hris_recruitment.delete_job_advertisement',
        'hris_recruitment.publish_job_advertisement',
        'hris_recruitment.close_job_advertisement',
    ]
    Permission.objects.filter(code__in=codes).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('hris_recruitment', '0004_jobadvertisement'),
        ('access_control', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_job_ad_permissions, remove_job_ad_permissions),
    ]
