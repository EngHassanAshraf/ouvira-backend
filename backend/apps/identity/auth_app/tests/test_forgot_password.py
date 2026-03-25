import time
from unittest.mock import patch
from django.urls import reverse
from django.core.cache import cache

from apps.identity.account.models.user import CustomUser
from apps.identity.auth_app.tests.base import BaseAuthTestCase


class ForgotPasswordTests(BaseAuthTestCase):
    """
    Tests for unauthenticated forgot password flow.
    Includes the timing oracle check and rate limiting.
    """

    def setUp(self):
        super().setUp()
        self.forgot_url = reverse("password-forgot")
        
        self.user = CustomUser.objects.create_user(
            username="forgotuser",
            email="known@ouvira.app",
            password="Password123!"
        )
        cache.clear()

    @patch("apps.identity.auth_app.services.password_reset_service.PasswordResetService._dispatch_reset_link")
    def test_unknown_email_returns_200(self, mock_dispatch):
        """Forgot PW: Unknown email returns HTTP 200 with identical body to known email"""
        # Test unknown email
        resp_unknown = self.client.post(self.forgot_url, {"identifier": "nobody@ouvira.app"}, format="json")
        self.assertEqual(resp_unknown.status_code, 200)
        self.assertIn("If an account with that identifier exists", resp_unknown.data["detail"])
        
        # Test known email
        resp_known = self.client.post(self.forgot_url, {"identifier": "known@ouvira.app"}, format="json")
        self.assertEqual(resp_known.status_code, 200)
        self.assertEqual(resp_unknown.data, resp_known.data)
        
        # Dispatch should only be called once (for the known email)
        self.assertEqual(mock_dispatch.call_count, 1)

    @patch("apps.identity.auth_app.services.password_reset_service.PasswordResetService._dispatch_reset_link")
    def test_unknown_phone_returns_200(self, mock_dispatch):
        """Forgot PW: Unknown phone returns HTTP 200 with identical body to known phone"""
        # Test unknown phone
        resp_unknown = self.client.post(self.forgot_url, {"identifier": "+19999999999"}, format="json")
        self.assertEqual(resp_unknown.status_code, 200)
        self.assertIn("If an account with that identifier exists", resp_unknown.data["detail"])
        
        # Test known phone
        resp_known = self.client.post(self.forgot_url, {"identifier": "+201234567891"}, format="json")
        self.assertEqual(resp_known.status_code, 200)
        self.assertEqual(resp_unknown.data, resp_known.data)

    @patch("apps.identity.auth_app.services.password_reset_service.PasswordResetService._dispatch_reset_link")
    @patch("apps.identity.auth_app.models.PasswordResetToken.objects.create")
    def test_timing_oracle_check(self, mock_create, mock_dispatch):
        """
        Forgot PW: Response time for unknown vs known email must not differ by more than 50ms
        Actually, in a test environment without a real DB delay, the time difference might be small.
        But we will measure it to ensure there is no artificial sleeping or massive logic gap.
        """
        # Warm up
        self.client.post(self.forgot_url, {"identifier": "warmup@ouvira.app"}, format="json")
        
        cache.clear()
        
        # Unknown
        t0 = time.perf_counter()
        self.client.post(self.forgot_url, {"identifier": "unknown_timing@ouvira.app"}, format="json")
        t1 = time.perf_counter()
        unknown_time = t1 - t0
        
        # Known
        t2 = time.perf_counter()
        self.client.post(self.forgot_url, {"identifier": "known@ouvira.app"}, format="json")
        t3 = time.perf_counter()
        known_time = t3 - t2
        
        diff_ms = abs(known_time - unknown_time) * 1000
        # The spec requires < 50ms absolute difference
        self.assertLess(diff_ms, 50.0, f"Timing difference {diff_ms:.2f}ms is > 50ms boundary")

    def test_rate_limit_4_requests_in_1_hour(self):
        """Forgot PW: Requesting reset 4 times in one hour returns 429 on the 4th request"""
        # 1st
        resp1 = self.client.post(self.forgot_url, {"identifier": "known@ouvira.app"}, format="json")
        self.assertEqual(resp1.status_code, 200)
        # 2nd
        resp2 = self.client.post(self.forgot_url, {"identifier": "known@ouvira.app"}, format="json")
        self.assertEqual(resp2.status_code, 200)
        # 3rd
        resp3 = self.client.post(self.forgot_url, {"identifier": "known@ouvira.app"}, format="json")
        self.assertEqual(resp3.status_code, 200)
        # 4th -> 429 Too Many Requests
        resp4 = self.client.post(self.forgot_url, {"identifier": "known@ouvira.app"}, format="json")
        self.assertEqual(resp4.status_code, 429)
        self.assertIn("Too many reset requests", resp4.data["detail"])
