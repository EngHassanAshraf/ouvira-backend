from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hris_recruitment', '0014_joboffer_offer_validity_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidatedocument',
            name='doc_type',
            field=models.CharField(
                choices=[
                    ('id_copy', 'ID Copy'),
                    ('qualification', 'Qualification Certificate'),
                    ('military_status', 'Military Status'),
                    ('personal_photo', 'Personal Photo'),
                    ('police_clearance', 'Police Clearance'),
                    ('birth_certificate', 'Birth Certificate'),
                    ('other', 'Other'),
                ],
                max_length=50,
            ),
        ),
    ]
