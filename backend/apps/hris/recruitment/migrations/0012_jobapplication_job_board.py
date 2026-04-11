from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hris_recruitment', '0011_seed_finalization_permissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobapplication',
            name='job_board',
            field=models.CharField(
                blank=True,
                choices=[
                    ('linkedin', 'LinkedIn'),
                    ('facebook', 'Facebook'),
                    ('bayt', 'Bayt'),
                    ('recommendation', 'Recommendation'),
                    ('internal', 'Internal'),
                    ('other', 'Other'),
                ],
                max_length=100,
                null=True,
            ),
        ),
    ]
