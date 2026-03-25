# Generated migration: auth_security_fixes
# Creates OTPRecord, PasswordResetToken tables and adds a partial unique index
# on PasswordResetToken(user_id) WHERE used = FALSE.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth_app", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # -------- OTPRecord --------
        migrations.CreateModel(
            name="OTPRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("identifier", models.CharField(help_text="Email address or phone number.", max_length=255)),
                ("channel", models.CharField(
                    choices=[("email", "Email"), ("sms", "SMS")],
                    help_text="Auto-detected from identifier format.",
                    max_length=5,
                )),
                ("otp_hash", models.CharField(max_length=64)),
                ("expires_at", models.DateTimeField()),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("is_verified", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(
                    blank=True,
                    help_text="Nullable \u2014 OTP may be issued before user account fully exists.",
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="otp_records",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "verbose_name": "OTP Record",
                "verbose_name_plural": "OTP Records",
                "db_table": "auth_otp_records",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="otprecord",
            index=models.Index(fields=["identifier", "channel", "is_verified"], name="otp_ident_chan_verified_idx"),
        ),
        migrations.AddIndex(
            model_name="otprecord",
            index=models.Index(fields=["identifier", "channel", "expires_at"], name="otp_ident_chan_expires_idx"),
        ),

        # -------- PasswordResetToken --------
        migrations.CreateModel(
            name="PasswordResetToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token_hash", models.CharField(db_index=True, max_length=64)),
                ("expires_at", models.DateTimeField()),
                ("used", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="password_reset_tokens",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "verbose_name": "Password Reset Token",
                "verbose_name_plural": "Password Reset Tokens",
                "db_table": "auth_password_reset_tokens",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="passwordresettoken",
            index=models.Index(fields=["user", "used"], name="pwreset_user_used_idx"),
        ),

        # Partial unique index — at most ONE active (used=False) token per user.
        # This is a database-level constraint that the service layer alone cannot guarantee.
        # It MUST be a partial index (not unique_together) because multiple USED tokens
        # per user are expected and valid.
        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX one_active_reset_token_per_user
                ON auth_password_reset_tokens (user_id)
                WHERE used = FALSE;
            """,
            reverse_sql="DROP INDEX IF EXISTS one_active_reset_token_per_user;",
        ),
    ]
