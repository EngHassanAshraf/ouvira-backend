from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="InternalLoginAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("identifier", models.CharField(help_text="Email or username used in the login attempt (stored for audit).", max_length=255)),
                ("company_id", models.IntegerField(blank=True, help_text="Company context resolved at login time.", null=True)),
                ("outcome", models.CharField(choices=[("success", "Success"), ("failure", "Failure"), ("locked", "Locked Out")], max_length=20)),
                ("failure_reason", models.CharField(blank=True, max_length=100)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="internal_login_attempts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Internal Login Attempt",
                "verbose_name_plural": "Internal Login Attempts",
                "db_table": "internal_auth_login_attempts",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["identifier", "created_at"], name="internal_auth_ident_idx"),
                    models.Index(fields=["user", "created_at"], name="internal_auth_user_idx"),
                    models.Index(fields=["outcome", "created_at"], name="internal_auth_outcome_idx"),
                ],
            },
        ),
    ]
