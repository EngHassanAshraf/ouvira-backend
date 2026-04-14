import inspect
from unittest.mock import patch
import importlib

from apps.identity.account.models.user import CustomUser
from django.test import override_settings
from django.core import mail

from apps.identity.auth_app.tasks.send_password_changed_email import send_password_changed_email
from apps.identity.auth_app.tasks.send_otp_email import send_otp_email
from apps.identity.auth_app.tasks.send_reset_email import send_reset_email
from apps.identity.auth_app.tests.base import BaseAuthTestCase

send_password_changed_email_module = importlib.import_module(
    "apps.identity.auth_app.tasks.send_password_changed_email"
)


class SecurityTasksTests(BaseAuthTestCase):
    """
    Tests for the background Celery notification tasks.
    """

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            username="taskuser",
            email="task@example.com",
            password="Password123!"
        )
        self.user.is_active = True
        self.user.email_verified = True
        self.user.save(update_fields=["is_active", "email_verified"])

    def test_send_password_changed_primitives(self):
        """
        Tasks: send_password_changed_email task receives only primitives.
        Assert no Django model instances in task kwargs/signature.
        """
        sig = inspect.signature(send_password_changed_email)
        
        # Check annotations
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            self.assertIn(param.annotation, (int, str), f"Parameter {param_name} is not a valid primitive type: {param.annotation}")
            self.assertNotEqual(param.annotation, CustomUser)

    def test_task_retries_on_smtp_failure(self):
        """Tasks: Retries on SMTP failure before giving up"""
        from celery.exceptions import Retry
        with patch.object(
            send_password_changed_email_module, "send_mail", side_effect=Exception("SMTP Connection Failed")
        ) as mock_send_mail, patch.object(
            send_password_changed_email, "retry", side_effect=Retry("Task is retrying")
        ):
            # In sync mode, calling self.retry() invokes the mock which raises Retry immediately.
            with self.assertRaises(Retry):
                send_password_changed_email(
                    user_id=self.user.id,
                    ip="127.0.0.1",
                    user_agent="Test Browser",
                    timestamp="2026-03-22T00:00:00+00:00"
                )
            self.assertEqual(mock_send_mail.call_count, 1)

    def test_task_failure_does_not_rollback_db(self):
        """Tasks: Task failure does not roll back the password change (they are decoupled)"""
        from celery.exceptions import Retry
        old_password = self.user.password
        from apps.identity.auth_app.services.password_change_service import PasswordChangeService

        with patch.object(
            send_password_changed_email_module, "send_mail", side_effect=Exception("SMTP Connection Failed")
        ), patch.object(
            send_password_changed_email, "retry", side_effect=Retry("Task is retrying")
        ):
            # The receiver swallows enqueue exceptions; password change must still persist.
            with self.captureOnCommitCallbacks(execute=True):
                PasswordChangeService.change_password(
                    user=self.user,
                    old_password="Password123!",
                    new_password="NewPassword123!",
                    ip="127.0.0.1",
                    user_agent="Test Browser"
                )

        self.user.refresh_from_db()
        self.assertNotEqual(self.user.password, old_password)
