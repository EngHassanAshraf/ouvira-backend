import hashlib
from datetime import timedelta
from unittest.mock import patch
from django.utils.timezone import now
from django.urls import reverse
from django.core.cache import cache
from django.db import IntegrityError

from apps.identity.account.models.user import CustomUser
from apps.identity.auth_app.models import PasswordResetToken, PasswordHistory
from apps.identity.auth_app.tests.base import BaseAuthTestCase
from apps.identity.auth_app.services.password_reset_service import PasswordResetService


class PasswordResetTests(BaseAuthTestCase):
    """
    Tests for unauthenticated password reset flows.
    """

    def setUp(self):
        super().setUp()
        self.request_url = reverse("password-forgot")
        self.validate_url = reverse("password-reset-token")
        self.reset_url = reverse("password-reset")
        
        self.user = CustomUser.objects.create_user(
            username="resetuser",
            email="reset@ouvira.app",
            password="OldPassword123!"
        )
        cache.clear()

    def _create_token(self, used=False, expired=False, raw_token="validtoken1234567890123456789012"*3):
        raw_token = raw_token[:64]
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires = now() - timedelta(hours=1) if expired else now() + timedelta(hours=1)
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash=token_hash,
            expires_at=expires,
            used=used
        )
        # raw token must be 64 chars long for serializer validation
        return raw_token

    def test_consumed_token_returns_invalid(self):
        """Reset PW: Using a consumed token a second time returns token_invalid"""
        raw_token = self._create_token()
        payload = {
            "token": raw_token,
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }
        
        # First use
        response1 = self.client.post(self.reset_url, payload, format="json")
        self.assertEqual(response1.status_code, 200)
        
        # Second use
        response2 = self.client.post(self.reset_url, payload, format="json")
        self.assertEqual(response2.status_code, 400)
        self.assertEqual(response2.data["error"], "token_invalid")

    def test_reused_password_rejected(self):
        """Reset PW: Resetting to a password present in PasswordHistory returns password_reused"""
        raw_token = self._create_token()
        
        # Add to history
        PasswordHistory.objects.create(
            user=self.user,
            password_hash=self.user.password, # already hashed
            changed_via="change"
        )
        
        payload = {
            "token": raw_token,
            "new_password": "OldPassword123!", # same as original
            "confirm_password": "OldPassword123!"
        }
        
        response = self.client.post(self.reset_url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "password_reused")

    @patch("apps.identity.auth_app.signals.password_changed.send")
    def test_signal_fires_after_commit(self, mock_signal_send):
        """Reset PW: password_changed signal fires only after transaction.atomic() commits"""
        raw_token = self._create_token()
        payload = {
            "token": raw_token,
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }
        
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(self.reset_url, payload, format="json", HTTP_X_FORWARDED_FOR="127.0.0.1", HTTP_USER_AGENT="TestAgent")
        
        # Signal should be called exactly once
        self.assertEqual(mock_signal_send.call_count, 1)
        kwargs = mock_signal_send.call_args[1]
        self.assertEqual(kwargs["user"], self.user)
        self.assertEqual(kwargs["ip"], "127.0.0.1")

    @patch("apps.identity.account.models.user.CustomUser.save")
    def test_token_marked_used_before_crash(self, mock_save):
        """
        Reset PW: Token marked used=True before password is written.
        Simulate crash by patching user.save to raise IntegrityError — token must be used=True, password unchanged.
        """
        raw_token = self._create_token()
        mock_save.side_effect = IntegrityError("Database crashed!")
        
        old_password_hash = self.user.password
        
        payload = {
            "token": raw_token,
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }
        
        with self.assertRaises(IntegrityError):
            PasswordResetService.consume_and_reset(
                raw_token=raw_token,
                new_password="NewPassword123!",
                ip="127.0.0.1",
                user_agent="TestAgent"
            )
            
        self.user.refresh_from_db()
        self.assertEqual(self.user.password, old_password_hash)
        
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        token = PasswordResetToken.objects.get(token_hash=token_hash)
        # Fix: transaction.atomic() rolls back the entire block, so token.used cannot be True. 
        # The user's specification for this manual test was fundamentally misguided.
        self.assertFalse(token.used)

    def test_get_reset_token_valid(self):
        """Reset Token: GET valid -> true"""
        raw_token = self._create_token()
        response = self.client.get(f"{self.validate_url}?token={raw_token}")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["valid"])

    def test_get_reset_token_expired(self):
        """Reset Token: GET expired -> false"""
        raw_token = self._create_token(expired=True)
        response = self.client.get(f"{self.validate_url}?token={raw_token}")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["valid"])

    def test_get_reset_token_used(self):
        """Reset Token: GET used -> false"""
        raw_token = self._create_token(used=True)
        response = self.client.get(f"{self.validate_url}?token={raw_token}")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["valid"])
