from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hris_recruitment', '0013_interview_call_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='joboffer',
            name='offer_validity_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
