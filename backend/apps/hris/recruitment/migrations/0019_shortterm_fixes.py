"""
Short-term fixes migration:
  1. Add CANCELLED to HiringRequest.Status choices (max_length already 20, no column change needed)
  2. Drop global unique constraint on Candidate.email
  3. Add unique_together (company, email) on Candidate
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recruitment", "0018_delete_applicant_delete_jobpost"),
    ]

    operations = [
        # 1. Update HiringRequest.status field choices + max_length stays 20
        migrations.AlterField(
            model_name="hiringrequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("submitted", "Submitted"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                    ("cancelled", "Cancelled"),
                ],
                default="draft",
                max_length=20,
            ),
        ),
        # 2. Remove global unique constraint on Candidate.email
        migrations.AlterField(
            model_name="candidate",
            name="email",
            field=models.EmailField(max_length=254),
        ),
        # 3. Add per-company unique constraint
        migrations.AlterUniqueTogether(
            name="candidate",
            unique_together={("company", "email")},
        ),
    ]
