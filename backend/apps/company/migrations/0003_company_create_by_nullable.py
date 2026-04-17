from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('company', '0002_phase1_employee_extensions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='create_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='created_companies',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
