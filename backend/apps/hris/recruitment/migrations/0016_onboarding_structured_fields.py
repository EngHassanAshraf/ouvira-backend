import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hris_recruitment', '0015_candidatedocument_birth_certificate'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='onboarding',
            name='session_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='onboarding',
            name='session_location',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='onboarding',
            name='assigned_mentor',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='mentored_onboardings',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='onboarding',
            name='attended',
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name='onboarding',
            name='engagement_level',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='onboarding',
            name='survey_link',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='onboarding',
            name='survey_responses',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
