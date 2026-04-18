from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hris_recruitment', '0012_jobapplication_job_board'),
    ]

    operations = [
        migrations.AddField(
            model_name='interview',
            name='call_status',
            field=models.CharField(
                blank=True,
                choices=[
                    ('not_answered', 'Not Answered'),
                    ('suitable', 'Suitable'),
                    ('call_back', 'Call Back'),
                ],
                max_length=20,
                null=True,
            ),
        ),
    ]
