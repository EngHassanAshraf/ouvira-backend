import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hris_recruitment', '0016_onboarding_structured_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='postprobationevaluation',
            name='tasks_score',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='postprobationevaluation',
            name='attendance_score',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='postprobationevaluation',
            name='initiative_score',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='postprobationevaluation',
            name='collaboration_score',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='postprobationevaluation',
            name='teamwork_score',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='postprobationevaluation',
            name='average_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='postprobationevaluation',
            name='evaluated_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='evaluations_as_evaluator',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='postprobationevaluation',
            name='workflow_status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('submitted_to_manager', 'Submitted to Manager'),
                    ('manager_approved', 'Manager Approved'),
                    ('hr_confirmed', 'HR Confirmed'),
                    ('final_decision', 'Final Decision'),
                ],
                default='draft',
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name='postprobationevaluation',
            name='manager_note',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='postprobationevaluation',
            name='hr_note',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='postprobationevaluation',
            name='rationale',
            field=models.TextField(blank=True),
        ),
    ]
