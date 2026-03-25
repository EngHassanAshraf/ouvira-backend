from django.urls import reverse
from unittest.mock import patch
from django.core.cache import cache

from apps.identity.account.models.user import CustomUser
from apps.identity.auth_app.models import PasswordHistory
from apps.identity.auth_app.tests.base import BaseAuthTestCase
from rest_framework_simplejwt.tokens import RefreshToken


class PasswordChangeTests(BaseAuthTestCase):
    """
    Tests for authenticated password change flow.
    """

    def setUp(self):
        super().setUp()
        self.change_url = reverse("password-change")
        
        self.user = CustomUser.objects.create_user(
            username="changeuser",
            email="change@ouvira.app",
            password="OldPassword123!"
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        cache.clear()

    def test_wrong_old_password_does_not_mutate(self):
        """Change PW: Wrong old pw returns wrong_password and does not mutate"""
        old_hash = self.user.password
        
        payload = {
            "old_password": "WrongPassword123!",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }
        response = self.client.post(self.change_url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "wrong_password")
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.password, old_hash)

    def test_reused_password_returns_password_reused(self):
        """Change PW: Reused returns password_reused"""
        # Save to history
        PasswordHistory.objects.create(
            user=self.user,
            password_hash=self.user.password,
            changed_via="reset"
        )
        
        payload = {
            "old_password": "OldPassword123!",
            "new_password": "OldPassword123!", # Reusing old
            "confirm_password": "OldPassword123!"
        }
        with patch("rest_framework.throttling.ScopedRateThrottle.allow_request", return_value=True):
            response = self.client.post(self.change_url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "password_reused")

    @patch("apps.identity.auth_app.signals.password_changed.send")
    def test_success_appends_history_and_signals(self, mock_signal):
        """Change PW: Success appends History and triggers signal"""
        self.assertEqual(PasswordHistory.objects.filter(user=self.user).count(), 0)
        
        payload = {
            "old_password": "OldPassword123!",
            "new_password": "NewPassword123!@",
            "confirm_password": "NewPassword123!@"
        }
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.change_url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        
        # Check history appended
        self.assertEqual(PasswordHistory.objects.filter(user=self.user).count(), 1)
        history = PasswordHistory.objects.filter(user=self.user).first()
        self.assertEqual(history.changed_via, "change")
        
        # Check signal fired
        self.assertEqual(mock_signal.call_count, 1)

    def test_unauthenticated_returns_401(self):
        """Change PW: Unauthenticated returns 401 (not 403, not 200)"""
        # Remove auth
        self.client.credentials()
        
        payload = {
            "old_password": "OldPassword123!",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }
        response = self.client.post(self.change_url, payload, format="json")
        self.assertEqual(response.status_code, 401)
