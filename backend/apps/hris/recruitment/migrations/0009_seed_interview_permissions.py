from django.db import migrations

def seed_interview_permissions(apps, schema_editor):
    Permission = apps.get_model('access_control', 'Permission')
    
    permissions = [
        ('hris_recruitment.view_interview', 'Recruitment', 'Can view interviews'),
        ('hris_recruitment.create_interview', 'Recruitment', 'Can schedule interviews'),
        ('hris_recruitment.update_interview', 'Recruitment', 'Can update interviews'),
        ('hris_recruitment.delete_interview', 'Recruitment', 'Can delete interviews'),
        ('hris_recruitment.record_interview_result', 'Recruitment', 'Can record interview results'),
        ('hris_recruitment.view_candidate_document', 'Recruitment', 'Can view candidate documents'),
        ('hris_recruitment.verify_candidate_document', 'Recruitment', 'Can verify candidate documents'),
    ]
    
    for code, module, description in permissions:
        Permission.objects.get_or_create(
            code=code,
            defaults={
                'module': module,
                'description': description
            }
        )

def remove_interview_permissions(apps, schema_editor):
    Permission = apps.get_model('access_control', 'Permission')
    codes = [
        'hris_recruitment.view_interview',
        'hris_recruitment.create_interview',
        'hris_recruitment.update_interview',
        'hris_recruitment.delete_interview',
        'hris_recruitment.record_interview_result',
        'hris_recruitment.view_candidate_document',
        'hris_recruitment.verify_candidate_document',
    ]
    Permission.objects.filter(code__in=codes).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('hris_recruitment', '0008_alter_candidate_options_alter_hiringrequest_options_and_more'),
        ('access_control', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_interview_permissions, remove_interview_permissions),
    ]
