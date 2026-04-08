from django.db import migrations

def seed_finalization_permissions(apps, schema_editor):
    Permission = apps.get_model('access_control', 'Permission')
    
    permissions = [
        ('hris_recruitment.view_job_offer', 'Recruitment', 'Can view job offers'),
        ('hris_recruitment.create_job_offer', 'Recruitment', 'Can create job offers'),
        ('hris_recruitment.update_job_offer', 'Recruitment', 'Can update job offers'),
        ('hris_recruitment.delete_job_offer', 'Recruitment', 'Can delete job offers'),
        ('hris_recruitment.accept_job_offer', 'Recruitment', 'Can accept job offers (Hiring Decision)'),
        ('hris_recruitment.view_onboarding', 'Recruitment', 'Can view onboarding'),
        ('hris_recruitment.update_onboarding', 'Recruitment', 'Can update onboarding tasks'),
    ]
    
    for code, module, description in permissions:
        Permission.objects.get_or_create(
            code=code,
            defaults={
                'module': module,
                'description': description
            }
        )

def remove_finalization_permissions(apps, schema_editor):
    Permission = apps.get_model('access_control', 'Permission')
    codes = [
        'hris_recruitment.view_job_offer',
        'hris_recruitment.create_job_offer',
        'hris_recruitment.update_job_offer',
        'hris_recruitment.delete_job_offer',
        'hris_recruitment.accept_job_offer',
        'hris_recruitment.view_onboarding',
        'hris_recruitment.update_onboarding',
    ]
    Permission.objects.filter(code__in=codes).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('hris_recruitment', '0010_alter_interview_interview_type_joboffer_onboarding_and_more'),
        ('access_control', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_finalization_permissions, remove_finalization_permissions),
    ]
