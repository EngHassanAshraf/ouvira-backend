from django.db import migrations

def seed_candidate_permissions(apps, schema_editor):
    Permission = apps.get_model('access_control', 'Permission')
    
    permissions = [
        ('hris_recruitment.view_candidate', 'Recruitment', 'Can view candidates'),
        ('hris_recruitment.create_candidate', 'Recruitment', 'Can create candidates'),
        ('hris_recruitment.update_candidate', 'Recruitment', 'Can update candidates'),
        ('hris_recruitment.delete_candidate', 'Recruitment', 'Can delete candidates'),
        ('hris_recruitment.view_job_application', 'Recruitment', 'Can view job applications'),
        ('hris_recruitment.move_to_stage', 'Recruitment', 'Can move application stage'),
        ('hris_recruitment.delete_job_application', 'Recruitment', 'Can delete job applications'),
    ]
    
    for code, module, description in permissions:
        Permission.objects.get_or_create(
            code=code,
            defaults={
                'module': module,
                'description': description
            }
        )

def remove_candidate_permissions(apps, schema_editor):
    Permission = apps.get_model('access_control', 'Permission')
    codes = [
        'hris_recruitment.view_candidate',
        'hris_recruitment.create_candidate',
        'hris_recruitment.update_candidate',
        'hris_recruitment.delete_candidate',
        'hris_recruitment.view_job_application',
        'hris_recruitment.move_to_stage',
        'hris_recruitment.delete_job_application',
    ]
    Permission.objects.filter(code__in=codes).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('hris_recruitment', '0006_candidate_jobapplication'),
        ('access_control', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_candidate_permissions, remove_candidate_permissions),
    ]
